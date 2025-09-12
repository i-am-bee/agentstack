/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
import * as jose from 'jose';
import NextAuth, { type DefaultSession } from 'next-auth';
import type { Provider } from 'next-auth/providers';
import Credentials from 'next-auth/providers/credentials';

import { ProviderList } from '#app/auth/providers/providerlist.ts';
import { AUTH_BASEPATH, OIDC_ENABLED } from '#utils/constants.ts';

let provider_list: {
  id: string;
  name: string;
  type: 'oidc';
  issuer: string;
  jwks_url: string;
  client_id: string;
  client_secret: string;
  nextauth_redirect_proxy_url: string;
  JWKS: {
    (protectedHeader?: jose.JWSHeaderParameters, token?: jose.FlattenedJWSInput): Promise<jose.CryptoKey>;
    coolingDown: boolean;
    fresh: boolean;
    reloading: boolean;
    reload: () => Promise<void>;
    jwks: () => jose.JSONWebKeySet | undefined;
  };
}[] = [];
if (OIDC_ENABLED) {
  try {
    provider_list = JSON.parse(process.env.OIDC_PROVIDERS || '[]');
    for (const provider of provider_list) {
      const JWKS = jose.createRemoteJWKSet(new URL(provider.jwks_url));
      provider.JWKS = JWKS;
    }
    console.log('Providers loaded.');
  } catch (parse_err) {
    console.warn('Unable to parse provider list');
    console.error(parse_err);
  }
}

declare module 'next-auth' {
  /**
   * Returned by `auth`, `useSession`, `getSession` and received as a prop on the `SessionProvider` React Context
   */
  interface Session {
    User: DefaultSession['user'];
    access_token?: string;
  }
}

import type { JWT } from 'next-auth/jwt';

declare module 'next-auth/jwt' {
  /** Returned by the `jwt` callback and `auth`, when using JWT sessions */
  interface JWT {
    /** OpenID ID Token */
    access_token?: string;
  }
}
// The providers come from a secret "oidc-providers" whos data is JSON and mounted in fs and loaded via import as json
const providers: Provider[] = [
  Credentials({
    credentials: { password: { label: 'Password', type: 'password' } },
    authorize(c) {
      if (c.password !== 'password') return null;
      return {
        id: 'test',
        name: 'Test User',
        email: 'test@example.com',
      };
    },
  }),
];

if (process.env.NEXTAUTH_SECRET) {
  const pList = new ProviderList();
  for (const prov of provider_list) {
    const pClass = pList.getProviderByName(prov.name.toLocaleLowerCase());
    if (pClass) {
      providers.push(
        pClass({
          id: prov.id,
          name: prov.name,
          type: prov.type,
          issuer: prov.issuer,
          clientId: prov.client_id,
          clientSecret: prov.client_secret,
          redirectProxyUrl: prov.nextauth_redirect_proxy_url,
          account(account: {
            refresh_token_expires_in: string;
            access_token: string;
            expires_at: string;
            refresh_token: string;
          }) {
            const refresh_token_expires_at = Math.floor(Date.now() / 1000) + Number(account.refresh_token_expires_in);
            return {
              access_token: account.access_token,
              expires_at: account.expires_at,
              refresh_token: account.refresh_token,
              refresh_token_expires_at,
            };
          },
        }),
      );
    }
  }
}

export const providerMap = providers
  .map((provider) => {
    if (typeof provider === 'function') {
      const providerData = provider();
      return { id: providerData.id, name: providerData.name };
    } else {
      return { id: provider.id, name: provider.name };
    }
  })
  .filter((provider) => provider.id !== 'credentials');

async function jwtWithRefresh(token, account) {
  if (account) {
    // First-time login, save the `access_token`, its expiry and the `refresh_token`
    return {
      ...token,
      access_token: account.access_token,
      expires_at: account.expires_at,
      refresh_token: account.refresh_token,
    };
  } else if (Date.now() < token.expires_at * 1000) {
    // Subsequent logins, but the `access_token` is still valid
    return token;
  } else {
    // Subsequent logins, but the `access_token` has expired, try to refresh it
    if (!token.refresh_token) throw new TypeError('Missing refresh_token');

    try {
      // The `token_endpoint` can be found in the provider's documentation. Or if they support OIDC,
      // at their `/.well-known/openid-configuration` endpoint.
      // lookup the provider's uri
      const tmp = providers.filter((p) => p.name === token['provider']);
      if (tmp.length === 0) {
        throw new TypeError('no matching provider found');
      }
      const tokenProvider = tmp[0];

      const response = await fetch(`${tokenProvider.options?.issuer}/token`, {
        method: 'POST',
        body: new URLSearchParams({
          client_id: '' + tokenProvider.options?.clientId || '',
          client_secret: '' + tokenProvider.options?.clientSecret || '',
          grant_type: 'refresh_token',
          refresh_token: token.refresh_token!,
        }),
      });

      const tokensOrError = await response.json();

      if (!response.ok) throw tokensOrError;

      const newTokens = tokensOrError as {
        access_token: string;
        expires_in: number;
        refresh_token?: string;
      };

      return {
        ...token,
        access_token: newTokens.access_token,
        expires_at: Math.floor(Date.now() / 1000 + newTokens.expires_in),
        // Some providers only issue refresh tokens once, so preserve if we did not get a new one
        refresh_token: newTokens.refresh_token ? newTokens.refresh_token : token.refresh_token,
      };
    } catch (error) {
      console.error('Error refreshing access_token', error);
      // If we fail to refresh the token, return an error so we can handle it on the page
      token.error = 'RefreshTokenError';
      return token;
    }
  }
}

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers,
  pages: {
    signIn: '/signin',
  },
  basePath: AUTH_BASEPATH,
  session: { strategy: 'jwt' },
  trustHost: true,
  useSecureCookies: true,
  cookies: {
    sessionToken: {
      name: `beeai-platform-1`,
      options: {
        httpOnly: true,
        sameSite: 'lax',
        path: '/',
        secure: true,
      },
    },
  },
  callbacks: {
    // middleware callback
    authorized({ auth }) {
      // essentially return !!auth
      if (!OIDC_ENABLED) {
        return true;
      }
      return !!auth;
    },
    async jwt({ token, account, trigger, session }) {
      if (trigger === 'update') {
        token.name = session.user.name;
      }
      // pull the id token out of the account on signIn
      if (account) {
        token['access_token'] = account.access_token;
        token['provider'] = account.provider;
      }
      return await jwtWithRefresh(token, account);
    },
    async session({ session, token }) {
      // Silly workaround to allow overriding the JWT interface
      const jwt: JWT = {};
      if (jwt && token?.access_token) {
        session.access_token = token.access_token;
      }
      return session;
    },
  },
});

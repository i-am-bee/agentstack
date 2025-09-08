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
    id_token: string;
    access_token?: string;
  }
}

import type { JWT, JWTDecodeParams, JWTEncodeParams } from 'next-auth/jwt';

declare module 'next-auth/jwt' {
  /** Returned by the `jwt` callback and `auth`, when using JWT sessions */
  interface JWT {
    /** OpenID ID Token */
    id_token?: string;
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

// Assisted by watsonx Code Assistant

/**
 * Asynchronously decodes a JWT using a list of providers.
 * This function attempts to verify the JWT against each provider's JWKS (JSON Web Key Set) URL.
 * It will retry up to a certain count if verification fails.
 *
 * @param {JWTDecodeParams} params - The parameters for JWT decoding.
 * @returns {Promise<JWT | null>} - A Promise that resolves to the decoded JWT object or null if decoding fails.
 */
async function internalDecode(params: JWTDecodeParams): Promise<JWT | null> {
  let jwt: JWT | null = null;
  let retryCount = 0;

  for (const provider of provider_list) {
    try {
      const { payload } = await jose.jwtVerify(params?.token || '', provider.JWKS, {
        issuer: provider.issuer,
        audience: provider.client_id,
      });
      payload['id_token'] = params?.token || '';
      jwt = payload;
      break;
    } catch (error) {
      if (error) {
        retryCount += 1;
      }
    }
  }
  if (jwt === null) {
    console.warn(`Unable to verify jwt, retries: ${retryCount}`);
  }
  return jwt;
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
  jwt: {
    async encode(params: JWTEncodeParams<JWT>): Promise<string> {
      // return a custom encoded JWT string
      return params?.token?.id_token || '';
    },
    async decode(params: JWTDecodeParams): Promise<JWT | null> {
      // return a `JWT` object, or `null` if decoding failed
      // const jwt = { access_token: params.token || '' };
      let jwt: JWT | null = null;
      jwt = await internalDecode(params);
      return jwt;
    },
  },
  cookies: {
    sessionToken: {
      name: `beeai-platform`,
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
    authorized({ request, auth }) {
      // essentially return !!auth
      const isOidcEnabled = process.env.OIDC_ENABLED === 'true';
      if (!isOidcEnabled) {
        return true;
      }
      const { pathname } = request.nextUrl;
      if (pathname === '/') return !!auth;
      return !!auth;
    },
    jwt({ token, account, trigger, session }) {
      if (trigger === 'update') {
        token.name = session.user.name;
      }
      // pull the id token out of the account on signIn
      if (account) {
        token['id_token'] = account.id_token;
        token['access_token'] = account.access_token;
      }
      return token;
    },
    async session({ session, token }) {
      if (token?.id_token) {
        session.id_token = token.id_token;
      } else {
        if (typeof token === 'string') {
          session.id_token = token;
        }
      }
      return session;
    },
  },
});

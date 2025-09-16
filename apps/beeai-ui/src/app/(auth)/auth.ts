/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
import * as jose from 'jose';
import NextAuth from 'next-auth';
import type { JWT } from 'next-auth/jwt';
import type { Provider } from 'next-auth/providers';

import { ProviderList } from '#app/api/auth/providers/providers.ts';
import { OIDC_ENABLED } from '#utils/constants.ts';
import { routes } from '#utils/router.ts';

import type { ProviderConfig } from './types';
import { jwtWithRefresh } from './utils';

let providersConfig: ProviderConfig[] = [];

const providers: Provider[] = [];

if (OIDC_ENABLED) {
  try {
    const providersJson = process.env.OIDC_PROVIDERS;
    if (!providersJson) {
      throw Error('No OIDC providers configured. Set OIDC_PROVIDERS with at least one provider.');
    }

    providersConfig = JSON.parse(providersJson);
    for (const provider of providersConfig) {
      const JWKS = jose.createRemoteJWKSet(new URL(provider.jwks_url));
      provider.JWKS = JWKS;
    }
  } catch (err) {
    console.error('Unable to parse providers from OIDC_PROVIDERS environment variable.', err);
  }

  const providerList = new ProviderList();
  for (const provider of providersConfig) {
    const { id, name, type, issuer, client_id, client_secret, nextauth_redirect_proxy_url } = provider;
    const providerClass = providerList.getProviderByName(name.toLocaleLowerCase());
    if (providerClass) {
      providers.push(
        providerClass({
          id,
          name,
          type,
          issuer,
          clientId: client_id,
          clientSecret: client_secret,
          redirectProxyUrl: nextauth_redirect_proxy_url,
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

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers,
  pages: {
    signIn: routes.login(),
  },
  session: { strategy: 'jwt' },
  trustHost: true,
  // Prevents nextauth errors when authentication is disabled and NEXTAUTH_SECRET is not provided
  secret: OIDC_ENABLED ? process.env.NEXTAUTH_SECRET : 'dummy_secret',
  useSecureCookies: true,
  cookies: {
    sessionToken: {
      name: 'beeai-platform',
      options: {
        httpOnly: true,
        sameSite: 'lax',
        path: '/',
        secure: process.env.NODE_ENV !== 'development',
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
      return await jwtWithRefresh(token, account, providers);
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

declare module 'next-auth' {
  /**
   * Returned by `auth`, `useSession`, `getSession` and received as a prop on the `SessionProvider` React Context
   */
  interface Session {
    access_token?: string;
  }
}

declare module 'next-auth/jwt' {
  /** Returned by the `jwt` callback and `auth`, when using JWT sessions */
  interface JWT {
    access_token?: string;
  }
}

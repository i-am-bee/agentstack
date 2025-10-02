/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import NextAuth from 'next-auth';
import type { Provider } from 'next-auth/providers';

import { getProviderConstructor } from '#app/(auth)/providers/providers.ts';
import { runtimeConfig } from '#contexts/App/runtime-config.ts';
import { routes } from '#utils/router.ts';

import type { ProviderConfig } from './types';
import { jwtWithRefresh, RefreshTokenError } from './utils';

let providersConfig: ProviderConfig[] = [];

const providers: Provider[] = [];

export const AUTH_COOKIE_NAME = 'beeai-platform';

const { isAuthEnabled } = runtimeConfig;

if (isAuthEnabled) {
  try {
    const providersJson = process.env.OIDC_PROVIDERS;
    if (!providersJson) {
      throw new Error('No OIDC providers configured. Set OIDC_PROVIDERS with at least one provider.');
    }

    providersConfig = JSON.parse(providersJson);
  } catch (err) {
    console.error('Unable to parse providers from OIDC_PROVIDERS environment variable.', err);
  }

  for (const provider of providersConfig) {
    const { id, name, issuer, client_id, client_secret } = provider;
    const providerConstructor = getProviderConstructor(name.toLocaleLowerCase());
    if (providerConstructor) {
      providers.push(
        providerConstructor({
          id,
          name,
          type: 'oidc',
          issuer,
          clientId: client_id,
          clientSecret: client_secret,
        }),
      );
    }
  }
}

export const authProviders = providers
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
    signIn: routes.signIn(),
  },
  session: { strategy: 'jwt' },
  trustHost: true,
  // Prevents nextauth errors when authentication is disabled and NEXTAUTH_SECRET is not provided
  secret: isAuthEnabled ? process.env.NEXTAUTH_SECRET : 'dummy_secret',
  cookies: {
    sessionToken: {
      name: AUTH_COOKIE_NAME,
      options: {
        httpOnly: true,
        sameSite: 'lax',
        path: '/',
      },
    },
  },
  callbacks: {
    authorized: ({ auth }) => {
      return isAuthEnabled ? Boolean(auth) : true;
    },
    jwt: async ({ token, account, trigger, session }) => {
      if (trigger === 'update') {
        token.name = session.user.name;
      }
      // pull the id token out of the account on signIn
      if (account) {
        token['access_token'] = account.access_token;
        token['provider'] = account.provider;
        token['refresh_token'] = account.refresh_token;
      }

      try {
        return await jwtWithRefresh(token, account, providers);
      } catch (error) {
        console.error('Error while refreshing jwt token:', error);

        if (error instanceof RefreshTokenError) {
          return null;
        }

        return token;
      }
    },
  },
});

declare module 'next-auth/jwt' {
  /** Returned by the `jwt` callback and `auth`, when using JWT sessions */
  interface JWT {
    access_token?: string;
    expires_at?: number;
    refresh_token?: string;
  }
}

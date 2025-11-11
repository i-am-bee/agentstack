/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import NextAuth from 'next-auth';

import { getProviderConstructor } from '#app/(auth)/providers/providers.ts';
import { runtimeConfig } from '#contexts/App/runtime-config.ts';
import { routes } from '#utils/router.ts';

import type { ProviderConfig, ProviderWithId } from './types';
import { getTokenRefreshSchedule, jwtWithRefresh, RefreshTokenError } from './utils';

let providersConfig: ProviderConfig[] = [];

const providers: ProviderWithId[] = [];

export const AUTH_COOKIE_NAME = 'agentstack';

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
    const { id, name, app, issuer, client_id, client_secret } = provider;
    const providerConstructor = getProviderConstructor(name.toLocaleLowerCase());
    if (providerConstructor && app === 'ui') {
      providers.push(
        providerConstructor({
          id,
          name,
          app,
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
        token.accessToken = account.access_token;
        token.provider = account.provider;
        token.refreshToken = account.refresh_token;
        token.expiresIn = account.expires_in;
        token.expiresAt = account.expires_at;
        token.refreshSchedule = getTokenRefreshSchedule(token.expiresAt);
      }

      try {
        const proactiveTokenRefresh = trigger === 'update' && Boolean(session?.proactiveTokenRefresh);
        return await jwtWithRefresh(token, providers, proactiveTokenRefresh);
      } catch (error) {
        console.error('Error while refreshing jwt token:', error);

        if (error instanceof RefreshTokenError) {
          return null;
        }

        return token;
      }
    },
    session({ session, token }) {
      session.refreshSchedule = token.refreshSchedule;

      return session;
    },
  },
});

interface TokenRefreshSchedule {
  checkInterval: number;
  refreshAt: number;
}

declare module 'next-auth/jwt' {
  /** Returned by the `jwt` callback and `auth`, when using JWT sessions */
  interface JWT {
    accessToken?: string;
    expiresAt?: number;
    refreshToken?: string;
    provider?: string;
    expiresIn?: number;
    refreshSchedule?: TokenRefreshSchedule;
  }
}

declare module 'next-auth' {
  interface Session {
    proactiveTokenRefresh?: boolean;
    refreshSchedule?: TokenRefreshSchedule;
  }
}

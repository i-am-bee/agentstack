/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import NextAuth from 'next-auth';
import { match } from 'ts-pattern';
import z from 'zod';

import { runtimeConfig } from '#contexts/App/runtime-config.ts';
import type { AuthProvider } from '#modules/auth/types.ts';
import { routes } from '#utils/router.ts';

import { Auth0Provider } from './providers/auth0';
import { IBMProvider } from './providers/ibm';
import type { ProviderWithId } from './types';
import { type ProviderConfig, providerConfigSchema } from './types';
import { getTokenRefreshSchedule, jwtWithRefresh, RefreshTokenError } from './utils';

let providersConfig: ProviderConfig[] = [];

export const AUTH_COOKIE_NAME = 'agentstack';

const { isAuthEnabled } = runtimeConfig;
3;
export function getAuthProviders(): AuthProvider[] {
  return getProviders()
    .filter((provider) => provider.id !== 'credentials')
    .map((provider) => {
      return { id: provider.id, name: provider.name };
    });
}

function getProviders(): ProviderWithId[] {
  const { isAuthEnabled } = runtimeConfig;

  if (!isAuthEnabled) {
    return [];
  }

  try {
    const providersJson = process.env.OIDC_PROVIDERS;
    if (!providersJson) {
      throw new Error('No OIDC providers configured. Set OIDC_PROVIDERS with at least one provider.');
    }

    providersConfig = z.array(providerConfigSchema).parse(JSON.parse(providersJson));

    return providersConfig.map((providerConfig) => {
      return match(providerConfig)
        .with({ name: 'w3id' }, { name: 'ibmid' }, { name: 'ibm' }, { name: 'ibmid-pkce' }, (provider) => {
          return IBMProvider({
            type: 'oidc',
            ...provider,
          });
        })
        .with({ name: 'auth0' }, (provider) => {
          return Auth0Provider(provider, provider.audience);
        })
        .exhaustive();
    });
  } catch (err) {
    console.error('Unable to parse providers from OIDC_PROVIDERS environment variable.', err);

    return [];
  }
}

const providers = getProviders();
console.log(providers);

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

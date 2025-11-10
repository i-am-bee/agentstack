/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { JWT } from 'next-auth/jwt';
import { coalesceAsync } from 'promise-coalesce';

import { cache, cacheKeys } from '#utils/server-cache.ts';

import { getTokenEndpoint } from './token-endpoint';
import type { ProviderWithId } from './types';

interface OIDCProviderOptions {
  clientId: string;
  clientSecret: string;
  issuer: string;
  [key: string]: unknown;
}

export async function jwtWithRefresh(
  token: JWT,
  providers: ProviderWithId[],
  proactiveTokenRefresh: boolean = false,
): Promise<JWT> {
  const triggerProactiveRefresh =
    proactiveTokenRefresh && token.refreshSchedule?.refreshAt && Date.now() >= token.refreshSchedule.refreshAt * 1000;

  if (token.expiresAt && Date.now() < token.expiresAt * 1000 && !triggerProactiveRefresh) {
    // Subsequent requests, `accessToken` is still valid
    return token;
  } else {
    const { refreshToken, provider } = token;
    // Subsequent requests, `accessToken` has expired, try to refresh it
    if (!refreshToken) {
      throw new TypeError('Missing refreshToken');
    }

    const tokenProvider = providers.find(({ id }) => id === provider);
    if (!tokenProvider) {
      throw new TypeError('No matching provider found');
    }

    // Type assertion to ensure we have the OIDC options
    const providerOptions = tokenProvider.options as OIDCProviderOptions | undefined;

    if (!providerOptions?.clientId || !providerOptions?.clientSecret || !providerOptions?.issuer) {
      throw new TypeError('Missing clientId, clientSecret, or issuer in provider configuration');
    }

    const { clientId, clientSecret, issuer: issuerUrl } = providerOptions;

    const refreshTokenUrl = await getTokenEndpoint(issuerUrl, clientId, clientSecret);

    const newTokens = await cache.getOrSet<RefreshTokenResult>(
      await cacheKeys.refreshToken(refreshToken),
      async () => {
        return await coalesceAsync(refreshToken, async () => {
          const response = await fetch(refreshTokenUrl, {
            method: 'POST',
            body: new URLSearchParams({
              client_id: clientId,
              client_secret: clientSecret,
              grant_type: 'refresh_token',
              refresh_token: refreshToken,
            }),
          });

          const tokensOrError = await response.json();

          if (!response.ok) {
            throw new RefreshTokenError('Error refreshing accessToken', tokensOrError);
          }

          return tokensOrError as RefreshTokenResult;
        });
      },
      // Prevent multiple refreshes until new accessToken is populated to the auth cookie
      { ttl: '1h' },
    );

    if (!newTokens) {
      throw new RefreshTokenError('Error refreshing accessToken');
    }

    const expiresAt = Math.floor(Date.now() / 1000 + newTokens.expires_in);
    return {
      ...token,
      accessToken: newTokens.access_token,
      expiresAt,
      expiresIn: newTokens.expires_in,
      // Some providers only issue refresh tokens once, so preserve if we did not get a new one
      refreshToken: newTokens.refresh_token ?? refreshToken,
      refreshSchedule: getTokenRefreshSchedule(expiresAt),
    };
  }
}

interface RefreshTokenErrorResponse {
  error: string;
  error_description?: string;
}
export class RefreshTokenError extends Error {
  errorResponse?: RefreshTokenErrorResponse;

  constructor(message: string, errorResponse?: RefreshTokenErrorResponse) {
    super(message);
    this.errorResponse = errorResponse;
  }
}

const TOKEN_REFRESH_THRESHOLD = 0.2;

interface RefreshTokenResult {
  access_token: string;
  expires_in: number;
  refresh_token?: string;
}

export function getTokenRefreshSchedule(expiresAt?: number) {
  if (!expiresAt) {
    return undefined;
  }

  const expiresIn = expiresAt - Date.now() / 1000;
  return {
    checkInterval: expiresIn * (TOKEN_REFRESH_THRESHOLD / 10),
    refreshAt: expiresAt - expiresIn * TOKEN_REFRESH_THRESHOLD,
  };
}

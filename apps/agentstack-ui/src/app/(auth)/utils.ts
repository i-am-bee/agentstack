/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Account } from 'next-auth';
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

function shortenToken(token?: string): string {
  return token ? `${token.substring(0, 8)}...${token.substring(token.length - 8)}` : 'undefined';
}

export async function jwtWithRefresh(
  token: JWT,
  providers: ProviderWithId[],
  earlyTokenRefresh: boolean = false,
): Promise<JWT> {
  console.log('----', shortenToken(token?.accessToken));

  if (
    token.expiresAt &&
    Date.now() < token.expiresAt * 1000 &&
    !(earlyTokenRefresh && Date.now() > token.expiresAt * 1000 - EARLY_REFRESH_TTL)
  ) {
    // Subsequent requests, `accessToken` is still valid
    return token;
  } else {
    // Subsequent requests, `accessToken` has expired, try to refresh it
    if (!token.refreshToken) {
      throw new TypeError('Missing refreshToken');
    }

    const tokenProvider = providers.find(({ id }) => id === token.provider);
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

    console.log('----------------------------------------');
    console.log('--- Requesting new access token');
    console.log(shortenToken(token.accessToken));

    const newTokens = await cache.getOrSet<RefreshTokenResult>(
      await cacheKeys.refreshToken(token.refreshToken),
      async () => {
        return await coalesceAsync(token.refreshToken!, async () => {
          console.log('--- Fetching access token for refreshToken:');
          console.log(shortenToken(token.refreshToken));

          const response = await fetch(refreshTokenUrl, {
            method: 'POST',
            body: new URLSearchParams({
              client_id: clientId,
              client_secret: clientSecret,
              grant_type: 'refreshToken',
              refreshToken: token.refreshToken!,
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

    console.log('------------------------------- SUCCESS:');
    console.log(shortenToken(newTokens?.accessToken));
    console.log(shortenToken(newTokens?.refreshToken));
    console.log('------------------------------- SUCCESS');

    return {
      ...token,
      accessToken: newTokens.accessToken,
      expiresAt: Math.floor(Date.now() / 1000 + newTokens.expires_in),
      expiresIn: newTokens.expires_in,
      // Some providers only issue refresh tokens once, so preserve if we did not get a new one
      refreshToken: newTokens.refreshToken ?? token.refreshToken,
    };
  }
}

const EARLY_REFRESH_TTL = 25_000; // 25 seconds

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

interface RefreshTokenResult {
  accessToken: string;
  expires_in: number;
  refreshToken?: string;
}

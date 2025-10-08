/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { truncate } from 'lodash';
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

export async function jwtWithRefresh(
  token: JWT,
  account: Account | null | undefined,
  providers: ProviderWithId[],
): Promise<JWT> {
  console.log('\n\njwtWithRefresh:\n', {
    access_token: truncate(token.access_token, { length: 10 }),
    expires: ((token.expires_at ?? 0) * 1000 - Date.now()) / 1000,
  });

  if (account) {
    // First-time login, save the `access_token`, its expiry and the `refresh_token`
    return {
      ...token,
      access_token: account.access_token,
      expires_at: account.expires_at,
      refresh_token: account.refresh_token,
    };
  } else if (token.expires_at && Date.now() < token.expires_at * 1000) {
    // Subsequent requests, `access_token` is still valid
    return token;
  } else {
    // Subsequent requests, `access_token` has expired, try to refresh it
    if (!token.refresh_token) {
      throw new TypeError('Missing refresh_token');
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

    console.log('\n\n\nRefreshing access_token\n', { refreshToken: token.refresh_token });

    const newTokens = await cache.getOrSet<RefreshTokenResult>(
      cacheKeys.refreshToken(token.refresh_token),
      async () => {
        return await coalesceAsync(token.refresh_token!, async () => {
          const response = await fetch(refreshTokenUrl, {
            method: 'POST',
            body: new URLSearchParams({
              client_id: clientId,
              client_secret: clientSecret,
              grant_type: 'refresh_token',
              refresh_token: token.refresh_token!,
            }),
          });

          const tokensOrError = await response.json();

          if (!response.ok) {
            throw new RefreshTokenError('Error refreshing access_token', tokensOrError);
          }

          // refreshTokenResultCache.set(token.refresh_token!, tokensOrError);

          return tokensOrError as RefreshTokenResult;
        });
      },
      { ttl: '1d' },
    );

    if (!newTokens) {
      throw new RefreshTokenError('Error refreshing access_token');
    }

    // let newTokens = refreshTokenResultCache.get(token.refresh_token);

    // if (!newTokens) {
    //   newTokens = await coalesceAsync(token.refresh_token, async () => {
    //     const response = await fetch(refreshTokenUrl, {
    //       method: 'POST',
    //       body: new URLSearchParams({
    //         client_id: clientId,
    //         client_secret: clientSecret,
    //         grant_type: 'refresh_token',
    //         refresh_token: token.refresh_token!,
    //       }),
    //     });

    //     const tokensOrError = await response.json();

    //     if (!response.ok) {
    //       throw new RefreshTokenError('Error refreshing access_token', tokensOrError);
    //     }

    //     refreshTokenResultCache.set(token.refresh_token!, tokensOrError);

    //     return tokensOrError as RefreshTokenResult;
    //   });
    // } else {
    //   console.log('\n\n--------------------------------------\nUSING CACHED REFRESH RESULT');
    // }

    console.log(
      `Refreshed access_token for provider\n`,
      {
        access_token: newTokens.access_token,
        refreshToken: newTokens.refresh_token,
      },
      '\n\n',
    );

    return {
      ...token,
      access_token: newTokens.access_token,
      expires_at: Math.floor(Date.now() / 1000 + newTokens.expires_in),
      // Some providers only issue refresh tokens once, so preserve if we did not get a new one
      refresh_token: newTokens.refresh_token ?? token.refresh_token,
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

interface RefreshTokenResult {
  access_token: string;
  expires_in: number;
  refresh_token?: string;
}

const refreshTokenResultCache = new Map<string, RefreshTokenResult>();

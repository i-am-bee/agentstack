/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { JWT } from 'next-auth/jwt';
import type { Provider } from 'next-auth/providers';

export async function jwtWithRefresh(token: JWT, account, providers: Provider[]): Promise<JWT> {
  if (account) {
    // First-time login, save the `access_token`, its expiry and the `refresh_token`
    return {
      ...token,
      access_token: account.access_token,
      expires_at: account.expires_at,
      refresh_token: account.refresh_token,
    };
  }
  // TODO: check if token.expires_at exists and is a number
  else if (Date.now() < Number(token.expires_at) * 1000) {
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
          refresh_token: String(token.refresh_token)!,
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
        refresh_token: newTokens.refresh_token ?? token.refresh_token,
      };
    } catch (error) {
      console.error('Error refreshing access_token', error);
      // If we fail to refresh the token, return an error so we can handle it on the page
      token.error = 'RefreshTokenError';
      return token;
    }
  }
}

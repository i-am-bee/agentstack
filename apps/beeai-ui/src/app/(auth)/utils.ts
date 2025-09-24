/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Account } from 'next-auth';
import type { JWT } from 'next-auth/jwt';
import type { Provider } from 'next-auth/providers';
import * as openidClient from 'openid-client';

interface OIDCProviderOptions {
  clientId: string;
  clientSecret: string;
  issuer: string;
  [key: string]: unknown;
}

export async function jwtWithRefresh(
  token: JWT,
  account: Account | null | undefined,
  providers: Provider[],
): Promise<JWT> {
  if (account) {
    // First-time login, save the `access_token`, its expiry and the `refresh_token`
    return {
      ...token,
      access_token: account.access_token,
      expires_at: account.expires_at,
      refresh_token: account.refresh_token,
    };
    // TODO: remove false, used for debugging
  } else if (token.expires_at && Date.now() < token.expires_at * 1000) {
    // Subsequent logins, but the `access_token` is still valid
    return token;
  } else {
    // Subsequent logins, but the `access_token` has expired, try to refresh it
    if (!token.refresh_token) throw new TypeError('Missing refresh_token');

    try {
      const tokenProvider = providers.find(({ name }) => name === token.provider);
      if (!tokenProvider) {
        throw new TypeError('No matching provider found');
      }

      // Type assertion to ensure we have the OIDC options
      const providerOptions = tokenProvider.options as OIDCProviderOptions | undefined;

      if (!providerOptions?.clientId || !providerOptions?.clientSecret || !providerOptions?.issuer) {
        throw new TypeError('Missing clientId, clientSecret, or issuer in provider configuration');
      }

      const { clientId, clientSecret, issuer: issuerUrl } = providerOptions;

      let refreshTokenUrl: string;

      try {
        // Try to discover the OIDC configuration and get the token endpoint
        const config = await openidClient.discovery(new URL(issuerUrl), clientId, clientSecret);
        const tokenEndpoint = config.serverMetadata().token_endpoint;

        if (!tokenEndpoint) {
          throw new Error('Token endpoint not found in OIDC discovery');
        }

        refreshTokenUrl = tokenEndpoint;
      } catch (discoveryError) {
        // Fallback: construct the token endpoint URL manually for OIDC
        console.warn('OIDC discovery failed, using fallback token endpoint:', discoveryError);
        refreshTokenUrl = `${issuerUrl.replace(/\/$/, '')}/token`;
      }

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
      return token;
    }
  }
}

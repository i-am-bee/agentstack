/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'server-only';

import * as openidClient from 'openid-client';

import { cache, cacheKeys } from '#utils/server-cache.ts';

export async function getTokenEndpoint(issuerUrl: string, clientId: string, clientSecret: string): Promise<string> {
  const tokenEndpoint = (await cache.get(cacheKeys.tokenEndpointUrl(issuerUrl))) as string | undefined;
  if (tokenEndpoint) {
    return tokenEndpoint;
  }

  try {
    // Perform OIDC discovery
    const config = await openidClient.discovery(new URL(issuerUrl), clientId, clientSecret);
    const tokenEndpoint = config.serverMetadata().token_endpoint;

    if (!tokenEndpoint) {
      throw new Error('Token endpoint not found in OIDC discovery');
    }

    await cache.set(cacheKeys.tokenEndpointUrl(issuerUrl), tokenEndpoint);

    return tokenEndpoint;
  } catch (discoveryError) {
    // Fallback: construct the token endpoint URL manually for OIDC
    const fallbackUrl = `${issuerUrl.replace(/\/$/, '')}/token`;
    console.error(`OIDC discovery failed for ${issuerUrl}, using fallback:`, discoveryError);

    return fallbackUrl;
  }
}

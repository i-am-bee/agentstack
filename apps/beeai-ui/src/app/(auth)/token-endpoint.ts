/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'server-only';

import * as openidClient from 'openid-client';

interface TokenEndpointCache {
  [issuerUrl: string]: string;
}

// In-memory cache for discovered token endpoints
const tokenEndpointCache: TokenEndpointCache = {};

export async function getTokenEndpoint(issuerUrl: string, clientId: string, clientSecret: string): Promise<string> {
  if (tokenEndpointCache[issuerUrl]) {
    return tokenEndpointCache[issuerUrl];
  }

  try {
    // Perform OIDC discovery
    const config = await openidClient.discovery(new URL(issuerUrl), clientId, clientSecret);
    const tokenEndpoint = config.serverMetadata().token_endpoint;

    if (!tokenEndpoint) {
      throw new Error('Token endpoint not found in OIDC discovery');
    }

    tokenEndpointCache[issuerUrl] = tokenEndpoint;

    return tokenEndpoint;
  } catch (discoveryError) {
    // Fallback: construct the token endpoint URL manually for OIDC
    const fallbackUrl = `${issuerUrl.replace(/\/$/, '')}/token`;
    console.error(`OIDC discovery failed for ${issuerUrl}, using fallback:`, discoveryError);

    return fallbackUrl;
  }
}

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { buildApiClient } from 'agentstack-sdk';

import { ensureToken } from '#app/(auth)/rsc.tsx';
import { runtimeConfig } from '#contexts/App/runtime-config.ts';
import { getBaseUrl } from '#utils/api/getBaseUrl.ts';

import { getProxyHeaders } from './utils';

function buildAuthenticatedAgentStackClient() {
  const { isAuthEnabled } = runtimeConfig;
  const baseUrl = getBaseUrl();

  const authenticatedFetch: typeof fetch = async (url, init) => {
    const request = new Request(url, init);

    if (isAuthEnabled) {
      const token = await ensureToken(request);

      if (token?.accessToken) {
        request.headers.set('Authorization', `Bearer ${token.accessToken}`);
      }
    }

    const isServer = typeof window === 'undefined';

    if (isServer) {
      const { headers } = await import('next/headers');
      const { forwarded, forwardedHost, forwardedFor, forwardedProto } = await getProxyHeaders(await headers());

      request.headers.set('forwarded', forwarded);

      if (forwardedHost) request.headers.set('x-forwarded-host', forwardedHost);
      if (forwardedProto) request.headers.set('x-forwarded-proto', forwardedProto);
      if (forwardedFor) request.headers.set('x-forwarded-for', forwardedFor);
    }

    const response = await fetch(request);

    return response;
  };

  const client = buildApiClient({ baseUrl, fetch: authenticatedFetch });

  return client;
}

export const agentStackClient = buildAuthenticatedAgentStackClient();

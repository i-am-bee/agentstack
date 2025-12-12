/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { buildApiClient } from 'agentstack-sdk';

import { ensureToken } from '#app/(auth)/rsc.tsx';
import { runtimeConfig } from '#contexts/App/runtime-config.ts';
import { listConnectorsResponseSchema } from '#modules/connectors/api/types.ts';
import { getBaseUrl } from '#utils/api/getBaseUrl.ts';

import { getProxyHeaders, handleFailedResponse } from './utils';

function buildAuthenticatedAgentstackClient() {
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

    if (!response.ok) {
      const error = await response.json();
      handleFailedResponse({ response, error });
    }

    return response;
  };

  const client = buildApiClient({ baseUrl, fetch: authenticatedFetch });
  return client;
}

const baseAgentstackClient = buildAuthenticatedAgentstackClient();

export const agentstackClient = {
  ...baseAgentstackClient,
  listConnectors: async () => {
    const response = await baseAgentstackClient.listConnectors();

    return listConnectorsResponseSchema.parse(response);
  },
};

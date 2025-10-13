/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { headers } from 'next/headers';
import type { Middleware } from 'openapi-fetch';
import createClient from 'openapi-fetch';

import { ensureToken } from '#app/(auth)/rsc.tsx';
import { runtimeConfig } from '#contexts/App/runtime-config.ts';
import { getBaseUrl } from '#utils/api/getBaseUrl.ts';
import { NEXTAUTH_URL } from '#utils/constants.ts';

import type { paths } from './schema';
import { getProxyHeaders } from './utils';

const authMiddleware: Middleware = {
  async onRequest({ request }) {
    let accessToken: string | undefined = undefined;

    if (runtimeConfig.isAuthEnabled) {
      const token = await ensureToken(request);

      if (token?.access_token) {
        accessToken = token.access_token;
      }
    }
    // add Authorization header to every request
    if (accessToken) {
      request.headers.set('Authorization', `Bearer ${accessToken}`);
    }
    return request;
  },
};

const proxyMiddleware: Middleware = {
  async onRequest({ request }) {
    const isServer = typeof window === 'undefined';
    if (isServer) {
      const { headers } = await import('next/headers');
      const { forwarded, forwardedHost, forwardedProto } = await getProxyHeaders(await headers());
      request.headers.set('forwarded', forwarded);
      if (forwardedHost) request.headers.set('x-forwarded-host', forwardedHost);
      if (forwardedProto) request.headers.set('x-forwarded-proto', forwardedProto);
    }
    return request;
  },
};

export const api = createClient<paths>({
  baseUrl: getBaseUrl(),
});

api.use(authMiddleware);
api.use(proxyMiddleware);

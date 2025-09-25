/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Middleware } from 'openapi-fetch';
import createClient from 'openapi-fetch';

import { getBaseUrl } from '#utils/api/getBaseUrl.ts';
import { OIDC_ENABLED } from '#utils/constants.ts';

import type { paths } from './schema';
import { ensureToken } from '#app/(auth)/rsc.tsx';

const authMiddleware: Middleware = {
  async onRequest({ request }) {
    let accessToken: string | undefined = undefined;

    if (OIDC_ENABLED) {
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

export const api = createClient<paths>({
  baseUrl: getBaseUrl(),
});

api.use(authMiddleware);

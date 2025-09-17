/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Middleware } from 'openapi-fetch';
import createClient from 'openapi-fetch';

import { auth } from '#app/(auth)/auth.ts';
import { getBaseUrl } from '#utils/api/getBaseUrl.ts';
import { OIDC_ENABLED } from '#utils/constants.ts';

import type { paths } from './schema';
let accessToken: string | undefined = undefined;

const authMiddleware: Middleware = {
  async onRequest({ request }) {
    // fetch token
    if (OIDC_ENABLED) {
      const session = await auth();

      if (session?.access_token) {
        accessToken = session.access_token;
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

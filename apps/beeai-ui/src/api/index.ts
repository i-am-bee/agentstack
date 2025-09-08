/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import createClient, { type Middleware } from 'openapi-fetch';

import { auth } from '#auth.ts';
import { getBaseUrl } from '#utils/api/getBaseUrl.ts';
import { OIDC_ENABLED } from '#utils/constants.ts';

import type { paths } from './schema';

let idToken: string | undefined = undefined;

const authMiddleware: Middleware = {
  async onRequest({ request }) {
    // fetch token, if it doesn’t exist
    if (!idToken && OIDC_ENABLED) {
      const authRes = await auth();
      if (authRes?.id_token) {
        idToken = authRes.id_token;
      }
    }
    // add Authorization header to every request
    if (idToken) {
      request.headers.set('Authorization', `Bearer ${idToken}`);
    }
    return request;
  },
};

export const api = createClient<paths>({
  baseUrl: getBaseUrl(),
});

api.use(authMiddleware);

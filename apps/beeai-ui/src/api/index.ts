/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import createClient from 'openapi-fetch';

import type { paths } from './schema';

export const api = createClient<paths>({
  baseUrl: '/',
});

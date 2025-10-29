/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Cacheable } from 'cacheable';

import { sha256Hash } from './hash';

export const cache = new Cacheable({
  ttl: 0, // cache items never expire by default
});

export const cacheKeys = {
  refreshToken: async (refreshToken: string) => `refreshToken:${await sha256Hash(refreshToken)}`,
  tokenEndpointUrl: (issuerUrl: string) => `tokenEndpoint:${issuerUrl}`,
};

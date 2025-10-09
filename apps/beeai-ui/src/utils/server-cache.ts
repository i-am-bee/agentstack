/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Cacheable } from 'cacheable';

export const cache = new Cacheable({
  ttl: 0, // cache items never expire by default
});

export const cacheKeys = {
  refreshToken: (refreshToken: string) => `refreshToken:${refreshToken}`,
  tokenEndpointUrl: (issuerUrl: string) => `tokenEndpoint:${issuerUrl}`,
};

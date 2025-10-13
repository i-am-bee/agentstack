/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Cacheable } from 'cacheable';
import { createHash } from 'crypto';

export const cache = new Cacheable({
  ttl: 0, // cache items never expire by default
});

export const cacheKeys = {
  refreshToken: (refreshToken: string) => `refreshToken:${createHash('sha256').update(refreshToken).digest('hex')}`,
  tokenEndpointUrl: (issuerUrl: string) => `tokenEndpoint:${issuerUrl}`,
};

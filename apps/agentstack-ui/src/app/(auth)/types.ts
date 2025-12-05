/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Provider } from 'next-auth/providers';
import z from 'zod';

const baseProviderConfigSchema = z.object({
  id: z.string(),
  name: z.string(),
  type: z.unknown().optional(),
  client_id: z.string(),
  client_secret: z.string(),
  issuer: z.string(),
});

const customProviderConfigSchema = baseProviderConfigSchema.extend({
  provider_type: z.literal('custom').optional(),
});

const auth0ProviderConfigSchema = baseProviderConfigSchema.extend({
  provider_type: z.literal('auth0'),
  audience: z.string(),
});

export const providerConfigSchema = z.preprocess(
  (val) => {
    if (typeof val === 'object' && val !== null && !('provider_type' in val)) {
      return { ...val, provider_type: 'custom' };
    }
    return val;
  },
  z.discriminatedUnion('provider_type', [auth0ProviderConfigSchema, customProviderConfigSchema]),
);

export type ProviderConfig = z.infer<typeof providerConfigSchema>;

export type ProviderWithId = Provider & { id: string };

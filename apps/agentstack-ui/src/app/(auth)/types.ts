/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Provider } from 'next-auth/providers';
import z from 'zod';

const baseOAuthConfigSchema = z.object({
  clientId: z.string(),
  clientSecret: z.string(),
  issuer: z.string(),
});

const baseProviderConfigSchema = z.object({
  id: z.string(),
  name: z.string(),
  type: z.unknown(),
  options: baseOAuthConfigSchema,
});

const auth0ProviderConfigSchema = baseProviderConfigSchema.extend({
  type: z.literal('auth0'),
  options: baseOAuthConfigSchema.extend({
    authorization: z.object({
      params: z.object({
        audience: z.string(),
      }),
    }),
  }),
});

const customProviderConfigSchema = baseProviderConfigSchema.extend({
  type: z.literal('custom'),
  options: baseOAuthConfigSchema,
});

export const providerConfigSchema = z.discriminatedUnion('type', [
  auth0ProviderConfigSchema,
  customProviderConfigSchema,
]);
export type ProviderConfig = z.infer<typeof providerConfigSchema>;

export type ProviderWithId = Provider & { id: string };

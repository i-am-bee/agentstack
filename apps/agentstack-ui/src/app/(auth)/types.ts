/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Provider } from 'next-auth/providers';
import z from 'zod';

const baseProviderConfigSchema = z.object({
  id: z.string(),
  name: z.unknown(),
  issuer: z.string(),
  client_id: z.string(),
  client_secret: z.string(),
});

const ibmProviderConfigSchema = baseProviderConfigSchema.extend({
  name: z.enum(['w3id', 'ibmid', 'ibm', 'ibmid-pkce']),
});

const auth0ProviderConfigSchema = baseProviderConfigSchema.extend({
  name: z.literal('auth0'),
  audience: z.string(),
});

export const providerConfigSchema = z.discriminatedUnion('name', [ibmProviderConfigSchema, auth0ProviderConfigSchema]);
export type ProviderConfig = z.infer<typeof providerConfigSchema>;

export type ProviderWithId = Provider & { id: string };

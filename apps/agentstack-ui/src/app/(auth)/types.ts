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

export type InternalProviderConfig =
  | {
      id: string;
      name: string;
      type: 'custom';
      options: {
        clientId: string;
        clientSecret: string;
        issuer: string;
      };
    }
  | {
      id: string;
      name: string;
      type: 'auth0';
      options: {
        clientId: string;
        clientSecret: string;
        issuer: string;
        authorization: {
          params: {
            audience: string;
          };
        };
      };
    };

export type ProviderWithId = Provider & { id: string };

export function transformToInternal(config: ProviderConfig): InternalProviderConfig {
  const baseOptions = {
    clientId: config.client_id,
    clientSecret: config.client_secret,
    issuer: config.issuer,
  };

  if (config.provider_type === 'auth0') {
    return {
      id: config.id,
      name: config.name,
      type: 'auth0',
      options: {
        ...baseOptions,
        authorization: {
          params: {
            audience: config.audience,
          },
        },
      },
    };
  }

  return {
    id: config.id,
    name: config.name,
    type: 'custom',
    options: baseOptions,
  };
}

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { A2AServiceExtension, A2AUiExtension } from 'beeai-sdk';
import { z } from 'zod';

const URI = 'https://a2a-extensions.beeai.dev/auth/secrets/v1';

const secretDemandSchema = z.object({
  name: z.string(),
  description: z.string().nullable(),
});
export type SecretDemand = z.infer<typeof secretDemandSchema>;

export const demandsSchema = z.object({
  secret_demands: z.record(z.string(), secretDemandSchema),
});
export type SecretDemands = z.infer<typeof demandsSchema>;

const fulfillmentSchema = z.object({
  secret_fulfillments: z.record(
    z.string(),
    z.object({
      secret: z.string(),
    }),
  ),
});
export type SecretFulfillment = z.infer<typeof fulfillmentSchema>;

export const secretsExtension: A2AServiceExtension<typeof URI, z.infer<typeof demandsSchema>, SecretFulfillment> = {
  getUri: () => URI,
  getDemandsSchema: () => demandsSchema,
  getFulfillmentSchema: () => fulfillmentSchema,
};

export const secretsMessageExtension: A2AUiExtension<typeof URI, SecretDemands> = {
  getMessageMetadataSchema: () => z.object({ [URI]: demandsSchema }).partial(),
  getUri: () => URI,
};

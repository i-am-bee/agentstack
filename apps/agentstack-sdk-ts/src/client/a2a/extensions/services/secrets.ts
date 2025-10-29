/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { z } from 'zod';

import type { A2AServiceExtension, A2AUiExtension } from '../types';

const URI = 'https://a2a-extensions.agentstack.beeai.dev/auth/secrets/v1';

const secretDemandSchema = z.object({
  name: z.string(),
  description: z.string().nullish(),
});
export type SecretDemand = z.infer<typeof secretDemandSchema>;

const secretDemandsSchema = z.object({
  secret_demands: z.record(z.string(), secretDemandSchema),
});
export type SecretDemands = z.infer<typeof secretDemandsSchema>;

const secretFulfillmentSchema = z.object({
  secret_fulfillments: z.record(
    z.string(),
    z.object({
      secret: z.string(),
    }),
  ),
});
export type SecretFulfillments = z.infer<typeof secretFulfillmentSchema>;

export const secretsExtension: A2AServiceExtension<
  typeof URI,
  z.infer<typeof secretDemandsSchema>,
  SecretFulfillments
> = {
  getUri: () => URI,
  getDemandsSchema: () => secretDemandsSchema,
  getFulfillmentSchema: () => secretFulfillmentSchema,
};

export const secretsMessageExtension: A2AUiExtension<typeof URI, SecretDemands> = {
  getMessageMetadataSchema: () => z.object({ [URI]: secretDemandsSchema }).partial(),
  getUri: () => URI,
};

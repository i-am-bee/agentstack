/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { A2AServiceExtension } from 'beeai-sdk';
import { z } from 'zod';

const URI = 'https://a2a-extensions.beeai.dev/services/embedding/v1';

const embeddingDemandSchema = z.object({
  description: z.string().nullable(),
  suggested: z.array(z.string()).nullable(),
});

export const demandsSchema = z.object({
  embedding_demands: z.record(z.string(), embeddingDemandSchema),
});
export type EmbeddingDemand = z.infer<typeof demandsSchema>;

const fulfillmentSchema = z.object({
  embedding_fulfillments: z.record(
    z.string(),
    z.object({
      identifier: z.string().optional(),
      api_base: z.string(),
      api_key: z.string(),
      api_model: z.string(),
    }),
  ),
});
export type EmbeddingFulfillment = z.infer<typeof fulfillmentSchema>;

export const embeddingExtension: A2AServiceExtension<
  typeof URI,
  z.infer<typeof demandsSchema>,
  EmbeddingFulfillment
> = {
  getUri: () => URI,
  getDemandsSchema: () => demandsSchema,
  getFulfillmentSchema: () => fulfillmentSchema,
};

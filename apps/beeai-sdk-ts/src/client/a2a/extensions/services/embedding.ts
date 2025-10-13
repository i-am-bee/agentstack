/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { z } from 'zod';

import type { A2AServiceExtension } from '../types';

const URI = 'https://a2a-extensions.beeai.dev/services/embedding/v1';

const embeddingDemandSchema = z.object({
  description: z.string().nullable(),
  suggested: z.array(z.string()).nullable(),
});

const embeddingDemandsSchema = z.object({
  embedding_demands: z.record(z.string(), embeddingDemandSchema),
});
export type EmbeddingDemand = z.infer<typeof embeddingDemandsSchema>;

const embeddingFulfillmentSchema = z.object({
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
export type EmbeddingFulfillment = z.infer<typeof embeddingFulfillmentSchema>;

export const embeddingExtension: A2AServiceExtension<
  typeof URI,
  z.infer<typeof embeddingDemandsSchema>,
  EmbeddingFulfillment
> = {
  getUri: () => URI,
  getDemandsSchema: () => embeddingDemandsSchema,
  getFulfillmentSchema: () => embeddingFulfillmentSchema,
};

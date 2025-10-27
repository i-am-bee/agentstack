/**
 * Copyright 2025 © Agent Stack a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { z } from 'zod';

import type { A2AServiceExtension } from '../types';

const URI = 'https://a2a-extensions.agentstack.dev/services/embedding/v1';

const embeddingDemandSchema = z.object({
  description: z.string().nullish(),
  suggested: z.array(z.string()).nullish(),
});

const embeddingDemandsSchema = z.object({
  embedding_demands: z.record(z.string(), embeddingDemandSchema),
});
export type EmbeddingDemands = z.infer<typeof embeddingDemandsSchema>;

const embeddingFulfillmentsSchema = z.object({
  embedding_fulfillments: z.record(
    z.string(),
    z.object({
      identifier: z.string().nullish(),
      api_base: z.string(),
      api_key: z.string(),
      api_model: z.string(),
    }),
  ),
});
export type EmbeddingFulfillments = z.infer<typeof embeddingFulfillmentsSchema>;

export const embeddingExtension: A2AServiceExtension<
  typeof URI,
  z.infer<typeof embeddingDemandsSchema>,
  EmbeddingFulfillments
> = {
  getUri: () => URI,
  getDemandsSchema: () => embeddingDemandsSchema,
  getFulfillmentSchema: () => embeddingFulfillmentsSchema,
};

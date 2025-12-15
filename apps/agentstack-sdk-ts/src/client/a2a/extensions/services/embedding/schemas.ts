/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

export const embeddingDemandSchema = z.object({
  description: z.string().nullish(),
  suggested: z.array(z.string()).nullish(),
});

export const embeddingDemandsSchema = z.object({
  embedding_demands: z.record(z.string(), embeddingDemandSchema),
});

export const embeddingFulfillmentSchema = z.object({
  identifier: z.string().nullish(),
  api_base: z.string(),
  api_key: z.string(),
  api_model: z.string(),
});

export const embeddingFulfillmentsSchema = z.object({
  embedding_fulfillments: z.record(z.string(), embeddingFulfillmentSchema),
});

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

export const llmDemandSchema = z.object({
  description: z.string().nullish(),
  suggested: z.array(z.string()).nullish(),
});

export const llmDemandsSchema = z.object({
  llm_demands: z.record(z.string(), llmDemandSchema),
});

export const llmFulfillmentSchema = z.object({
  identifier: z.string().nullish(),
  api_base: z.string(),
  api_key: z.string(),
  api_model: z.string(),
});

export const llmFulfillmentsSchema = z.object({
  llm_fulfillments: z.record(z.string(), llmFulfillmentSchema),
});

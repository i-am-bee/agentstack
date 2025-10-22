/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { z } from 'zod';

import type { A2AServiceExtension } from '../types';

const URI = 'https://a2a-extensions.beeai.dev/services/llm/v1';

const llmDemandSchema = z.object({
  description: z.string().nullish(),
  suggested: z.array(z.string()).nullish(),
});

const llmDemandsSchema = z.object({
  llm_demands: z.record(z.string(), llmDemandSchema),
});
export type LLMDemands = z.infer<typeof llmDemandsSchema>;

const llmFulfillmentSchema = z.object({
  llm_fulfillments: z.record(
    z.string(),
    z.object({
      identifier: z.string().nullish(),
      api_base: z.string(),
      api_key: z.string(),
      api_model: z.string(),
    }),
  ),
});
export type LLMFulfillments = z.infer<typeof llmFulfillmentSchema>;

export const llmExtension: A2AServiceExtension<typeof URI, z.infer<typeof llmDemandsSchema>, LLMFulfillments> = {
  getUri: () => URI,
  getDemandsSchema: () => llmDemandsSchema,
  getFulfillmentSchema: () => llmFulfillmentSchema,
};

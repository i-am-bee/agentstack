/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { A2AServiceExtension } from 'beeai-sdk';
import { z } from 'zod';

const URI = 'https://a2a-extensions.beeai.dev/services/llm/v1';

const llmDemandSchema = z.object({
  description: z.string().nullable(),
  suggested: z.array(z.string()).nullable(),
});

export const demandsSchema = z.object({
  llm_demands: z.record(z.string(), llmDemandSchema),
});
export type LLMDemand = z.infer<typeof demandsSchema>;

const fulfillmentSchema = z.object({
  llm_fulfillments: z.record(
    z.string(),
    z.object({
      identifier: z.string().optional(),
      api_base: z.string(),
      api_key: z.string(),
      api_model: z.string(),
    }),
  ),
});
export type LLMFulfillment = z.infer<typeof fulfillmentSchema>;

export const llmExtension: A2AServiceExtension<typeof URI, z.infer<typeof demandsSchema>, LLMFulfillment> = {
  getUri: () => URI,
  getDemandsSchema: () => demandsSchema,
  getFulfillmentSchema: () => fulfillmentSchema,
};

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { A2AServiceExtension } from '../../../../core/extensions/types';
import { llmDemandsSchema, llmFulfillmentsSchema } from './schemas';
import type { LLMDemands, LLMFulfillments } from './types';

const URI = 'https://a2a-extensions.agentstack.beeai.dev/services/llm/v1';

export const llmExtension: A2AServiceExtension<typeof URI, LLMDemands, LLMFulfillments> = {
  getUri: () => URI,
  getDemandsSchema: () => llmDemandsSchema,
  getFulfillmentsSchema: () => llmFulfillmentsSchema,
};

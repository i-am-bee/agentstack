/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { LLMDemands, LLMFulfillments } from '../../a2a/extensions/services/llm/types';
import type { ContextToken } from '../../api/contexts/types';
import { unwrapResult } from '../../api/core/client';
import type { AgentStackClient } from '../../api/core/types';
import { ModelCapability } from '../../api/model-providers/types';

const DEFAULT_SCORE_CUTOFF = 0.4;

export const buildLLMExtensionFulfillmentResolver = (api: AgentStackClient, token: ContextToken) => {
  return async ({ llm_demands }: LLMDemands): Promise<LLMFulfillments> => {
    const allDemands = Object.keys(llm_demands);
    const fulfillmentPromises = allDemands.map(async (demandKey) => {
      const demand = llm_demands[demandKey];
      const resolvedModels = unwrapResult(
        await api.matchModelProviders({
          suggested_models: demand.suggested ?? [],
          capability: ModelCapability.Llm,
          score_cutoff: DEFAULT_SCORE_CUTOFF,
        }),
      );

      if (resolvedModels.items.length === 0) {
        throw new Error(`No models found for demand ${demandKey}. Demand details: ${JSON.stringify(demand)}`);
      }

      return [
        demandKey,
        {
          identifier: 'llm_proxy',
          // {platform_url} is replaced by the server SDK to the platform URL
          api_base: '{platform_url}/api/v1/openai/',
          api_key: token.token,
          api_model: resolvedModels.items[0].model_id,
        },
      ] as const;
    });

    const fulfilledEntries = await Promise.all(fulfillmentPromises);

    return { llm_fulfillments: Object.fromEntries(fulfilledEntries) };
  };
};

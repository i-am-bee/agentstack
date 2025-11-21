/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { AgentstackClient } from '../../../api/build-api-client';
import type { ContextToken } from '../../../api/types';
import { ModelCapability } from '../../../api/types';
import type { LLMDemands, LLMFulfillments } from '../services/llm';

const DEFAULT_SCORE_CUTOFF = 0.4;

export const buildLLMExtensionFulfillmentResolver = (api: AgentstackClient, token: ContextToken) => {
  return async ({ llm_demands }: LLMDemands): Promise<LLMFulfillments> => {
    const allDemands = Object.keys(llm_demands);
    const fulfillmentPromises = allDemands.map(async (demandKey) => {
      const demand = llm_demands[demandKey];
      const resolvedModels = await api.matchProviders({
        suggestedModels: demand.suggested ?? [],
        capability: ModelCapability.Llm,
        scoreCutoff: DEFAULT_SCORE_CUTOFF,
      });

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

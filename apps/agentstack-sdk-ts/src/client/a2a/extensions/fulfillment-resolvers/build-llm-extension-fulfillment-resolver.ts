/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { AgentstackClient } from '../../../api/build-api-client';
import { ContextToken, ModelCapability } from '../../../api/types';
import { LLMDemands, LLMFulfillments } from '../services/llm';

export const buildLLMExtensionFulfillmentResolver = (api: AgentstackClient, token: ContextToken) => {
  return async ({ llm_demands }: LLMDemands): Promise<LLMFulfillments> => {
    const allDemands = Object.keys(llm_demands);
    const fullfillemnts: LLMFulfillments = { llm_fulfillments: {} };

    for (const demandKey of allDemands) {
      const demand = llm_demands[demandKey];
      const resolvedModels = await api.matchProviders(demand.suggested ?? [], ModelCapability.Llm, 0.4);

      if (resolvedModels.items.length === 0) {
        console.error(demand);
        throw new Error(`No models found for demand ${demandKey}`);
      }

      fullfillemnts.llm_fulfillments[demandKey] = {
        identifier: 'llm_proxy',
        api_base: '{platform_url}/api/v1/openai/',
        api_key: token.token,
        api_model: resolvedModels.items[0].model_id,
      };
    }

    return fullfillemnts;
  };
};

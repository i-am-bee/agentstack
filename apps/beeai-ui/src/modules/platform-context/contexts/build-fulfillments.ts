/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Fulfillments } from '#api/a2a/types.ts';

interface BuildFullfilmentsParams {
  platformToken: string;
  selectedProviders: Record<string, string>;
}

export const buildFullfilments = ({ platformToken, selectedProviders }: BuildFullfilmentsParams): Fulfillments => {
  return {
    mcp: async () => {
      throw new Error('MCP fulfillment not implemented');
    },
    llm: async ({ llm_demands }) => {
      const allDemands = Object.keys(llm_demands);
      if (allDemands.length !== 1) {
        throw new Error('Platform currently support single demand LLM');
      }

      return allDemands.reduce(
        (memo, demandKey) => {
          if (!selectedProviders[demandKey]) {
            throw new Error(`Selected provider for demand ${demandKey} not found`);
          }

          memo.llm_fulfillments[demandKey] = {
            identifier: 'llm_proxy',
            api_base: '{platform_url}/api/v1/openai/',
            api_key: platformToken,
            api_model: selectedProviders[demandKey],
          };

          return memo;
        },
        { llm_fulfillments: {} },
      );
    },
  };
};

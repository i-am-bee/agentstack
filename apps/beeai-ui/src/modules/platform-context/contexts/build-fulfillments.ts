/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Fulfillments } from '#api/a2a/types.ts';

export const buildFullfilments = (platformToken: string): Fulfillments => {
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
          memo.llm_fulfillments[demandKey] = {
            identifier: 'llm_proxy',
            api_base: '{platform_url}/api/v1/llm/',
            api_key: platformToken,
            api_model: 'dummy',
          };

          return memo;
        },
        { llm_fulfillments: {} },
      );
    },
  };
};

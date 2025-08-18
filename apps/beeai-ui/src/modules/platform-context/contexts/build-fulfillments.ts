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
    llm: async () => {
      return {
        llm_fulfillments: {
          default: {
            identifier: 'llm_proxy',
            api_base: '{platform_url}/api/v1/llm/',
            api_key: platformToken,
            api_model: 'dummy',
          },
        },
      };
    },
  };
};

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { EmbeddingDemand } from '#api/a2a/extensions/services/embedding.ts';
import type { SecretDemands } from '#api/a2a/extensions/services/secrets.ts';
import type { Fulfillments } from '#api/a2a/types.ts';
import type { AgentRequestSecrets } from '#modules/runs/contexts/agent-secrets/types.ts';
import { BASE_URL } from '#utils/constants.ts';
import type { FeatureFlags } from '#utils/feature-flags.ts';

import type { ContextToken } from './platform-context';

interface BuildFullfilmentsParams {
  contextToken: ContextToken;
  selectedLLMProviders: Record<string, string>;
  selectedEmbeddingProviders: Record<string, string>;
  selectedMCPServers: Record<string, string>;
  requestedSecrets: AgentRequestSecrets;
  featureFlags: FeatureFlags;
  selectedOpenRouterModel: null | { model: string; key: string };
}

export const buildFullfilments = ({
  contextToken,
  selectedLLMProviders,
  selectedEmbeddingProviders,
  selectedMCPServers,
  requestedSecrets,
  featureFlags,
  selectedOpenRouterModel,
}: BuildFullfilmentsParams): Fulfillments => {
  return {
    getContextToken: () => contextToken,

    secrets: async ({ secret_demands }: SecretDemands, runtimeFullfilledDemands?: AgentRequestSecrets) => {
      const demanded_fullfilments = Object.entries(secret_demands).reduce(
        (memo, [key]) => {
          const getFullfilment = () => {
            const fullfilment = requestedSecrets[key];
            if (fullfilment.isReady) {
              return fullfilment.value;
            }

            return null;
          };

          const fullfilment = getFullfilment();

          if (fullfilment !== null) {
            memo.secret_fulfillments[key] = {
              secret: fullfilment,
            };
          }

          return memo;
        },
        { secret_fulfillments: {} },
      );

      if (runtimeFullfilledDemands) {
        return {
          ...demanded_fullfilments,
          secret_fulfillments: {
            ...demanded_fullfilments.secret_fulfillments,
            ...Object.entries(runtimeFullfilledDemands).reduce((memo, [key, value]) => {
              if (value.isReady) {
                memo[key] = { secret: value.value };
              }

              return memo;
            }, {}),
          },
        };
      } else {
        return demanded_fullfilments;
      }
    },

    embedding: async ({ embedding_demands }: EmbeddingDemand) => {
      const allDemands = Object.keys(embedding_demands);

      return allDemands.reduce(
        (memo, demandKey) => {
          if (!selectedEmbeddingProviders[demandKey]) {
            throw new Error(`Selected provider for Embedding demand ${demandKey} not found`);
          }

          memo.embedding_fulfillments[demandKey] = {
            identifier: 'embedding_proxy',
            api_base: '{platform_url}/api/v1/openai/',
            api_key: contextToken.token,
            api_model: selectedEmbeddingProviders[demandKey],
          };

          return memo;
        },
        { embedding_fulfillments: {} },
      );
    },
    llm: async ({ llm_demands }) => {
      const allDemands = Object.keys(llm_demands);

      return allDemands.reduce(
        (memo, demandKey) => {
          if (!selectedOpenRouterModel) {
            throw new Error('Selected open router model not found');
          }

          memo.llm_fulfillments[demandKey] = {
            identifier: 'llm_proxy',
            api_base: 'https://openrouter.ai/api/v1/',
            api_key: selectedOpenRouterModel.key,
            api_model: selectedOpenRouterModel.model,
          };

          // if (!featureFlags.ModelProviders) {
          //   memo.llm_fulfillments[demandKey] = {
          //     identifier: 'llm_proxy',
          //     api_base: '{platform_url}/api/v1/openai/',
          //     api_key: contextToken.token,
          //     api_model: 'dummy',
          //   };

          //   return memo;
          // }

          // if (!selectedLLMProviders[demandKey]) {
          //   throw new Error(`Selected provider for LLM demand ${demandKey} not found`);
          // }

          return memo;
        },
        { llm_fulfillments: {} },
      );
    },
    mcp: async ({ mcp_demands }) => {
      if (!featureFlags.MCP) {
        return null;
      }

      const allDemands = Object.keys(mcp_demands);

      return allDemands.reduce(
        (memo, demandKey) => {
          memo.mcp_fulfillments[demandKey] = {
            transport: {
              type: 'streamable_http',
              url: selectedMCPServers[demandKey],
            },
          };

          return memo;
        },
        { mcp_fulfillments: {} },
      );
    },
    oauth: async () => {
      if (!featureFlags.MCPOAuth) {
        return null;
      }

      return {
        oauth_fulfillments: {
          default: {
            redirect_uri: `${BASE_URL}/oauth-callback`,
          },
        },
      };
    },
  };
};

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { AgentSettings, ContextToken, EmbeddingDemands, FormFulfillments, Fulfillments } from 'agentstack-sdk';

import { BASE_URL } from '#utils/constants.ts';
import type { FeatureFlags } from '#utils/feature-flags.ts';

interface BuildFulfillmentsParams {
  contextToken: ContextToken;
  selectedLLMProviders: Record<string, string>;
  selectedEmbeddingProviders: Record<string, string>;
  selectedMCPServers: Record<string, string>;
  providedSecrets: Record<string, string>;
  selectedSettings: AgentSettings;
  formFulfillments: FormFulfillments | null;
  oauthRedirectUri: string | null;
  featureFlags: FeatureFlags;
}

export const buildFulfillments = ({
  contextToken,
  selectedLLMProviders,
  selectedEmbeddingProviders,
  selectedMCPServers,
  selectedSettings,
  providedSecrets,
  formFulfillments,
  oauthRedirectUri,
  featureFlags,
}: BuildFulfillmentsParams): Fulfillments => {
  return {
    getContextToken: () => contextToken,

    settings: async () => {
      return {
        values: selectedSettings,
      };
    },

    form: async () => {
      return formFulfillments;
    },

    secrets: async () => {
      const resolvedSecrets = Object.entries(providedSecrets).reduce(
        (memo, [key, value]) => {
          memo.secret_fulfillments[key] = {
            secret: value,
          };
          return memo;
        },
        { secret_fulfillments: {} },
      );

      return resolvedSecrets;
    },

    embedding: async ({ embedding_demands }: EmbeddingDemands) => {
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
          if (!featureFlags.ModelProviders) {
            memo.llm_fulfillments[demandKey] = {
              identifier: 'llm_proxy',
              api_base: '{platform_url}/api/v1/openai/',
              api_key: contextToken.token,
              api_model: 'dummy',
            };

            return memo;
          }

          if (!selectedLLMProviders[demandKey]) {
            throw new Error(`Selected provider for LLM demand ${demandKey} not found`);
          }

          memo.llm_fulfillments[demandKey] = {
            identifier: 'llm_proxy',
            api_base: '{platform_url}/api/v1/openai/',
            api_key: contextToken.token,
            api_model: selectedLLMProviders[demandKey],
          };

          return memo;
        },
        { llm_fulfillments: {} },
      );
    },
    mcp: async ({ mcp_demands }) => {
      if (!featureFlags.MCP) {
        return {
          mcp_fulfillments: {},
        };
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
      return {
        oauth_fulfillments: {
          default: {
            redirect_uri: `${BASE_URL}/oauth-callback`,
          },
        },
      };
    },
    oauthRedirectUri: () => {
      return oauthRedirectUri;
    },
  };
};

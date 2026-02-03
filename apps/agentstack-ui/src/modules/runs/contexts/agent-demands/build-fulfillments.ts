/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type {
  Connector,
  ContextToken,
  EmbeddingDemands,
  FormFulfillments,
  Fulfillments,
  MCPFulfillments,
  SettingsDemands,
  SettingsFormValues,
} from 'agentstack-sdk';
import { ConnectorState, MCPTransportType } from 'agentstack-sdk';

import { transformSettingsFormValuesToLegacySettingsValues } from '#modules/runs/settings/utils.ts';
import { BASE_URL } from '#utils/constants.ts';

interface BuildFulfillmentsParams {
  contextToken: ContextToken;
  selectedLLMProviders: Record<string, string>;
  selectedEmbeddingProviders: Record<string, string>;
  providedSecrets: Record<string, string>;
  legacySettingsDemands: SettingsDemands | null;
  settingsFormDemanded: boolean;
  selectedSettings: SettingsFormValues;
  formFulfillments: FormFulfillments;
  oauthRedirectUri: string | null;
  connectors: Connector[];
}

export const buildFulfillments = ({
  contextToken,
  selectedLLMProviders,
  selectedEmbeddingProviders,
  selectedSettings,
  legacySettingsDemands,
  settingsFormDemanded,
  providedSecrets,
  formFulfillments,
  oauthRedirectUri,
  connectors,
}: BuildFulfillmentsParams): Fulfillments => {
  const fulfillments: Fulfillments = {
    // @deprecated - token now passed via A2A client headers
    getContextToken: () => contextToken,

    form: async (demands) => {
      if (demands.form_demands.initial_form && !formFulfillments.form_fulfillments.initial_form) {
        throw new Error('Initial form has not been fulfilled despite being demanded.');
      }

      if (!demands.form_demands.settings_form && formFulfillments.form_fulfillments.settings_form) {
        const form_fulfillments = { ...formFulfillments.form_fulfillments };

        delete form_fulfillments.settings_form;

        return { form_fulfillments };
      }

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
      const connectedConnectors = connectors.filter((connector) => connector.state === ConnectorState.Connected);
      const allDemands = Object.keys(mcp_demands);
      const mcp_fulfillments: MCPFulfillments['mcp_fulfillments'] = {};

      for (const demandKey of allDemands) {
        const demand = mcp_demands[demandKey];
        const suggestedNames = demand.suggested || [];

        // TODO: what if we have multiple connectors with the same name?
        // currently we just randomly pick the latest connector
        const matchingConnectors = connectedConnectors.filter((connector) =>
          suggestedNames.some(
            (suggestedName) => connector.metadata?.name?.toLowerCase() === suggestedName.toLowerCase(),
          ),
        );

        if (matchingConnectors.length > 0) {
          const latestConnector = matchingConnectors[matchingConnectors.length - 1];

          mcp_fulfillments[demandKey] = {
            transport: {
              type: MCPTransportType.StreamableHttp,
              url: `{platform_url}/api/v1/connectors/${latestConnector.id}/mcp`,
            },
          };
        }
      }

      return { mcp_fulfillments };
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

  if (legacySettingsDemands && !settingsFormDemanded) {
    // @deprecated - use form extension with "settings_form" demand instead
    fulfillments.settings = async () => ({
      values: transformSettingsFormValuesToLegacySettingsValues(selectedSettings),
    });
  }

  return fulfillments;
};

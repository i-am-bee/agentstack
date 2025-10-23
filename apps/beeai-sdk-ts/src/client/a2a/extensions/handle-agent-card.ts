/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { AgentCapabilities } from '@a2a-js/sdk';

import type { ContextToken } from '../../context/types';
import type { EmbeddingDemands, EmbeddingFulfillments } from './services/embedding';
import { embeddingExtension } from './services/embedding';
import type { LLMDemands, LLMFulfillments } from './services/llm';
import { llmExtension } from './services/llm';
import type { MCPDemands, MCPFulfillments } from './services/mcp';
import { mcpExtension } from './services/mcp';
import type { OAuthDemands, OAuthFulfillments } from './services/oauth-provider';
import { oauthProviderExtension } from './services/oauth-provider';
import { platformApiExtension } from './services/platform';
import type { SecretDemands, SecretFulfillments } from './services/secrets';
import { secretsExtension } from './services/secrets';
import type { FormDemands, FormFullfillments } from './ui/form';
import { formExtension } from './ui/form';
import { oauthRequestExtension } from './ui/oauth';
import type { SettingsDemands, SettingsFullfillments } from './ui/settings';
import { settingsExtension } from './ui/settings';
import { extractServiceExtensionDemands, fulfillServiceExtensionDemand } from './utils';

export interface Fulfillments {
  llm: (demand: LLMDemands) => Promise<LLMFulfillments>;
  embedding: (demand: EmbeddingDemands) => Promise<EmbeddingFulfillments>;
  mcp: (demand: MCPDemands) => Promise<MCPFulfillments>;
  oauth: (demand: OAuthDemands) => Promise<OAuthFulfillments>;
  settings: (demand: SettingsDemands) => Promise<SettingsFullfillments>;
  secrets: (demand: SecretDemands) => Promise<SecretFulfillments>;
  form: (demand: FormDemands) => Promise<FormFullfillments | null>;
  oauthRedirectUri: () => string | null;
  getContextToken: () => ContextToken;
}

const mcpExtensionExtractor = extractServiceExtensionDemands(mcpExtension);
const llmExtensionExtractor = extractServiceExtensionDemands(llmExtension);
const embeddingExtensionExtractor = extractServiceExtensionDemands(embeddingExtension);
const oauthExtensionExtractor = extractServiceExtensionDemands(oauthProviderExtension);
const settingsExtensionExtractor = extractServiceExtensionDemands(settingsExtension);
const secretExtensionExtractor = extractServiceExtensionDemands(secretsExtension);
const formExtensionExtractor = extractServiceExtensionDemands(formExtension);

const fullfillMcpDemand = fulfillServiceExtensionDemand(mcpExtension);
const fullfillLlmDemand = fulfillServiceExtensionDemand(llmExtension);
const fullfillEmbeddingDemand = fulfillServiceExtensionDemand(embeddingExtension);
const fullfillOAuthDemand = fulfillServiceExtensionDemand(oauthProviderExtension);
const fullfillSettingsDemand = fulfillServiceExtensionDemand(settingsExtension);
const fullfillSecretDemand = fulfillServiceExtensionDemand(secretsExtension);
const fullfillFormDemand = fulfillServiceExtensionDemand(formExtension);

export const handleAgentCard = (agentCard: { capabilities: AgentCapabilities }) => {
  const extensions = agentCard.capabilities.extensions ?? [];

  const llmDemands = llmExtensionExtractor(extensions);
  const embeddingDemands = embeddingExtensionExtractor(extensions);
  const mcpDemands = mcpExtensionExtractor(extensions);
  const oauthDemands = oauthExtensionExtractor(extensions);
  const settingsDemands = settingsExtensionExtractor(extensions);
  const secretDemands = secretExtensionExtractor(extensions);
  const formDemands = formExtensionExtractor(extensions);

  const resolveMetadata = async (fullfillments: Fulfillments) => {
    let fullfilledMetadata = {};

    fullfilledMetadata = platformApiExtension(fullfilledMetadata, fullfillments.getContextToken());

    if (llmDemands) {
      fullfilledMetadata = fullfillLlmDemand(fullfilledMetadata, await fullfillments.llm(llmDemands));
    }

    if (embeddingDemands) {
      fullfilledMetadata = fullfillEmbeddingDemand(fullfilledMetadata, await fullfillments.embedding(embeddingDemands));
    }

    if (mcpDemands) {
      fullfilledMetadata = fullfillMcpDemand(fullfilledMetadata, await fullfillments.mcp(mcpDemands));
    }

    if (oauthDemands) {
      fullfilledMetadata = fullfillOAuthDemand(fullfilledMetadata, await fullfillments.oauth(oauthDemands));
    }

    if (settingsDemands) {
      fullfilledMetadata = fullfillSettingsDemand(fullfilledMetadata, await fullfillments.settings(settingsDemands));
    }

    if (secretDemands) {
      fullfilledMetadata = fullfillSecretDemand(fullfilledMetadata, await fullfillments.secrets(secretDemands));
    }

    if (formDemands) {
      const formFullfilment = await fullfillments.form(formDemands);
      if (formFullfilment) {
        fullfilledMetadata = fullfillFormDemand(fullfilledMetadata, formFullfilment);
      }
    }

    const oauthRedirectUri = fullfillments.oauthRedirectUri();
    if (oauthRedirectUri) {
      fullfilledMetadata = {
        ...fullfilledMetadata,
        [oauthRequestExtension.getUri()]: {
          redirect_uri: oauthRedirectUri,
        },
      };
    }

    return fullfilledMetadata;
  };

  return {
    resolveMetadata,
    demands: { llmDemands, embeddingDemands, mcpDemands, oauthDemands, settingsDemands, secretDemands, formDemands },
  };
};

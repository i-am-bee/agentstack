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
import type { FormDemands, FormFulfillments } from './services/form';
import { formExtension } from './services/form';
import { oauthRequestExtension } from './ui/oauth';
import type { SettingsDemands, SettingsFulfillments } from './ui/settings';
import { settingsExtension } from './ui/settings';
import { extractServiceExtensionDemands, fulfillServiceExtensionDemand } from './utils';

export interface Fulfillments {
  llm: (demand: LLMDemands) => Promise<LLMFulfillments>;
  embedding: (demand: EmbeddingDemands) => Promise<EmbeddingFulfillments>;
  mcp: (demand: MCPDemands) => Promise<MCPFulfillments>;
  oauth: (demand: OAuthDemands) => Promise<OAuthFulfillments>;
  settings: (demand: SettingsDemands) => Promise<SettingsFulfillments>;
  secrets: (demand: SecretDemands) => Promise<SecretFulfillments>;
  form: (demand: FormDemands) => Promise<FormFulfillments>;
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

const fulfillMcpDemand = fulfillServiceExtensionDemand(mcpExtension);
const fulfillLlmDemand = fulfillServiceExtensionDemand(llmExtension);
const fulfillEmbeddingDemand = fulfillServiceExtensionDemand(embeddingExtension);
const fulfillOAuthDemand = fulfillServiceExtensionDemand(oauthProviderExtension);
const fulfillSettingsDemand = fulfillServiceExtensionDemand(settingsExtension);
const fulfillSecretDemand = fulfillServiceExtensionDemand(secretsExtension);
const fulfillFormDemand = fulfillServiceExtensionDemand(formExtension);

export const handleAgentCard = (agentCard: { capabilities: AgentCapabilities }) => {
  const extensions = agentCard.capabilities.extensions ?? [];

  const llmDemands = llmExtensionExtractor(extensions);
  const embeddingDemands = embeddingExtensionExtractor(extensions);
  const mcpDemands = mcpExtensionExtractor(extensions);
  const oauthDemands = oauthExtensionExtractor(extensions);
  const settingsDemands = settingsExtensionExtractor(extensions);
  const secretDemands = secretExtensionExtractor(extensions);
  const formDemands = formExtensionExtractor(extensions);

  const resolveMetadata = async (fulfillments: Fulfillments) => {
    let fulfilledMetadata = {};

    fulfilledMetadata = platformApiExtension(fulfilledMetadata, fulfillments.getContextToken());

    if (llmDemands) {
      fulfilledMetadata = fulfillLlmDemand(fulfilledMetadata, await fulfillments.llm(llmDemands));
    }

    if (embeddingDemands) {
      fulfilledMetadata = fulfillEmbeddingDemand(fulfilledMetadata, await fulfillments.embedding(embeddingDemands));
    }

    if (mcpDemands) {
      fulfilledMetadata = fulfillMcpDemand(fulfilledMetadata, await fulfillments.mcp(mcpDemands));
    }

    if (oauthDemands) {
      fulfilledMetadata = fulfillOAuthDemand(fulfilledMetadata, await fulfillments.oauth(oauthDemands));
    }

    if (settingsDemands) {
      fulfilledMetadata = fulfillSettingsDemand(fulfilledMetadata, await fulfillments.settings(settingsDemands));
    }

    if (secretDemands) {
      fulfilledMetadata = fulfillSecretDemand(fulfilledMetadata, await fulfillments.secrets(secretDemands));
    }

    if (formDemands) {
      fulfilledMetadata = fulfillFormDemand(fulfilledMetadata, await fulfillments.form(formDemands));
    }

    const oauthRedirectUri = fulfillments.oauthRedirectUri();
    if (oauthRedirectUri) {
      fulfilledMetadata = {
        ...fulfilledMetadata,
        [oauthRequestExtension.getUri()]: {
          redirect_uri: oauthRedirectUri,
        },
      };
    }

    return fulfilledMetadata;
  };

  return {
    resolveMetadata,
    demands: { llmDemands, embeddingDemands, mcpDemands, oauthDemands, settingsDemands, secretDemands, formDemands },
  };
};

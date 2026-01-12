/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { oauthExtension, oauthRequestExtension } from '../a2a/extensions/auth/oauth';
import { secretsExtension } from '../a2a/extensions/auth/secrets';
import { embeddingExtension } from '../a2a/extensions/services/embedding';
import { formExtension } from '../a2a/extensions/services/form';
import { llmExtension } from '../a2a/extensions/services/llm';
import { mcpExtension } from '../a2a/extensions/services/mcp';
import { platformApiExtension } from '../a2a/extensions/services/platform-api';
import { settingsExtension } from '../a2a/extensions/ui/settings';
import type { AgentCapabilities } from '../a2a/protocol/types';
import { extractServiceExtensionDemands } from './extensions/extract';
import { fulfillServiceExtensionDemand } from './extensions/fulfill';
import type { Fulfillments } from './extensions/types';

const mcpExtensionExtractor = extractServiceExtensionDemands(mcpExtension);
const llmExtensionExtractor = extractServiceExtensionDemands(llmExtension);
const embeddingExtensionExtractor = extractServiceExtensionDemands(embeddingExtension);
const oauthExtensionExtractor = extractServiceExtensionDemands(oauthExtension);
const settingsExtensionExtractor = extractServiceExtensionDemands(settingsExtension);
const secretExtensionExtractor = extractServiceExtensionDemands(secretsExtension);
const formExtensionExtractor = extractServiceExtensionDemands(formExtension);

const fulfillMcpDemand = fulfillServiceExtensionDemand(mcpExtension);
const fulfillLlmDemand = fulfillServiceExtensionDemand(llmExtension);
const fulfillEmbeddingDemand = fulfillServiceExtensionDemand(embeddingExtension);
const fulfillOAuthDemand = fulfillServiceExtensionDemand(oauthExtension);
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
    let fulfilledMetadata: Record<string, unknown> = {};

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
    demands: {
      llmDemands,
      embeddingDemands,
      mcpDemands,
      oauthDemands,
      settingsDemands,
      secretDemands,
      formDemands,
    },
  };
};

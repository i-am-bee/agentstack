/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { AgentSettings, FormFulfillments } from 'agentstack-sdk';
import { type PropsWithChildren, useCallback, useEffect, useState } from 'react';

import type { AgentA2AClient } from '#api/a2a/types.ts';
import { useApp } from '#contexts/App/index.ts';
import type { RunFormValues } from '#modules/form/types.ts';
import { useCreateContextToken } from '#modules/platform-context/api/mutations/useCreateContextToken.ts';
import { useMatchProviders } from '#modules/platform-context/api/mutations/useMatchProviders.ts';
import { usePlatformContext } from '#modules/platform-context/contexts/index.ts';
import { ModelCapability } from '#modules/platform-context/types.ts';
import { getSettingsDemandsDefaultValues } from '#modules/runs/settings/utils.ts';

import { useAgentSecrets } from '../agent-secrets';
import type { FulfillmentsContext } from './agent-demands-context';
import { AgentDemandsContext } from './agent-demands-context';
import { buildFulfillments } from './build-fulfillments';

interface Props<UIGenericPart> {
  agentClient: AgentA2AClient<UIGenericPart>;
}

export function AgentDemandsProvider<UIGenericPart>({
  agentClient,
  children,
}: PropsWithChildren<Props<UIGenericPart>>) {
  const { demandedSecrets } = useAgentSecrets();

  const [selectedEmbeddingProviders, setSelectedEmbeddingProviders] = useState<Record<string, string>>({});
  const [selectedLLMProviders, setSelectedLLMProviders] = useState<Record<string, string>>({});
  const [formFulfillments, setFormFulfillments] = useState<FormFulfillments>({ form_fulfillments: {} });

  const [selectedSettings, setSelectedSettings] = useState<AgentSettings>(
    getSettingsDemandsDefaultValues(agentClient.demands.settingsDemands ?? { fields: [] }),
  );

  const {
    config: { featureFlags },
  } = useApp();
  const { contextId } = usePlatformContext();

  const { mutateAsync: createContextToken } = useCreateContextToken();

  const onUpdateSettings = useCallback((value: AgentSettings) => {
    setSelectedSettings(value);
  }, []);

  const setDefaultSelectedLLMProviders = useCallback(
    (data: Record<string, string[]>) => {
      setSelectedLLMProviders(
        Object.fromEntries(
          Object.entries(data).map(([key, value]) => {
            if (value.length === 0) {
              throw new Error(`No match found for demand ${key}`);
            }

            return [key, value[0]];
          }),
        ),
      );
    },
    [setSelectedLLMProviders],
  );

  const { data: matchedLLMProviders } = useMatchProviders({
    demands: agentClient?.demands.llmDemands?.llm_demands ?? {},
    onSuccess: setDefaultSelectedLLMProviders,
    capability: ModelCapability.Llm,
  });

  const setDefaultSelectedEmbeddingProviders = useCallback(
    (data: Record<string, string[]>) => {
      setSelectedEmbeddingProviders(
        Object.fromEntries(
          Object.entries(data).map(([key, value]) => {
            if (value.length === 0) {
              throw new Error(`No match found for demand ${key}`);
            }

            return [key, value[0]];
          }),
        ),
      );
    },
    [setSelectedEmbeddingProviders],
  );

  const { data: matchedEmbeddingProviders } = useMatchProviders({
    demands: agentClient?.demands.embeddingDemands?.embedding_demands ?? {},
    onSuccess: setDefaultSelectedEmbeddingProviders,
    capability: ModelCapability.Embedding,
  });

  const selectLLMProvider = useCallback(
    (key: string, value: string) => {
      setSelectedLLMProviders((prev) => ({ ...prev, [key]: value }));
    },
    [setSelectedLLMProviders],
  );

  const selectEmbeddingProvider = useCallback(
    (key: string, value: string) => {
      setSelectedEmbeddingProviders((prev) => ({ ...prev, [key]: value }));
    },
    [setSelectedEmbeddingProviders],
  );

  const provideFormValues = useCallback(
    (values: RunFormValues) => {
      setFormFulfillments((prev) => {
        prev.form_fulfillments['initial_form'] = { values };
        return prev;
      });
    },
    [setFormFulfillments],
  );

  const [selectedMCPServers, setSelectedMCPServers] = useState<Record<string, string>>({});

  useEffect(() => {
    setSelectedMCPServers(
      Object.keys(agentClient?.demands.mcpDemands?.mcp_demands ?? {}).reduce(
        (memo, value) => ({
          ...memo,
          [value]: '',
        }),
        {},
      ),
    );
  }, [agentClient?.demands.mcpDemands?.mcp_demands]);

  const selectMCPServer = useCallback(
    (key: string, value: string) => {
      setSelectedMCPServers((prev) => ({ ...prev, [key]: value }));
    },
    [setSelectedMCPServers],
  );

  const getContextToken = useCallback(async () => {
    if (contextId === null) {
      throw new Error('Illegal State - Context ID is not set.');
    }

    const contextToken = await createContextToken({
      context_id: contextId,
      grant_global_permissions: {
        llm: ['*'],
        a2a_proxy: [],
        contexts: [],
        embeddings: ['*'],
        feedback: [],
        files: [],
        providers: [],
        provider_variables: [],
        model_providers: [],
        mcp_providers: [],
        mcp_proxy: [],
        mcp_tools: [],
        vector_stores: [],
        context_data: [],
      },
      grant_context_permissions: {
        files: ['*'],
        vector_stores: ['*'],
        context_data: ['*'],
      },
    });

    if (!contextToken) {
      throw new Error('Could not generate context token');
    }

    return contextToken;
  }, [contextId, createContextToken]);

  const getFulfillments = useCallback(
    async (fulfillmentsContext: FulfillmentsContext) => {
      const contextToken = await getContextToken();

      const providedSecrets = demandedSecrets.reduce((memo, secret) => {
        if (secret.isReady) {
          memo[secret.key] = secret.value;
        }
        return memo;
      }, fulfillmentsContext.providedSecrets ?? {});

      return buildFulfillments({
        contextToken,
        selectedLLMProviders,
        selectedEmbeddingProviders,
        selectedMCPServers,
        providedSecrets,
        featureFlags,
        selectedSettings,
        formFulfillments,
        oauthRedirectUri: fulfillmentsContext.oauthRedirectUri ?? null,
      });
    },
    [
      getContextToken,
      selectedLLMProviders,
      selectedEmbeddingProviders,
      selectedMCPServers,
      featureFlags,
      selectedSettings,
      demandedSecrets,
      formFulfillments,
    ],
  );

  return (
    <AgentDemandsContext.Provider
      value={{
        matchedLLMProviders,
        selectedLLMProviders,
        matchedEmbeddingProviders,
        selectedEmbeddingProviders,
        provideFormValues,
        getFulfillments,
        selectLLMProvider,
        selectEmbeddingProvider,
        selectMCPServer,
        selectedMCPServers,
        selectedSettings,
        settingsDemands: agentClient?.demands.settingsDemands ?? null,
        formDemands: agentClient?.demands.formDemands ?? null,
        onUpdateSettings,
      }}
    >
      {children}
    </AgentDemandsContext.Provider>
  );
}

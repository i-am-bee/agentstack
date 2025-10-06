/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { type PropsWithChildren, useCallback, useEffect, useState } from 'react';

import type { AgentA2AClient } from '#api/a2a/types.ts';
import { useApp } from '#contexts/App/index.ts';
import { useCreateContextToken } from '#modules/platform-context/api/mutations/useCreateContextToken.ts';
import {
  useMatchEmbeddingProviders,
  useMatchLLMProviders,
} from '#modules/platform-context/api/mutations/useMatchProviders.ts';
import { usePlatformContext } from '#modules/platform-context/contexts/index.ts';

import { useAgentSecrets } from '../agent-secrets';
import { AgentDemandsContext } from './agent-demands-context';
import { buildFullfilments } from './build-fulfillments';

interface Props<UIGenericPart> {
  agentClient?: AgentA2AClient<UIGenericPart>;
}

export function AgentDemandsProvider<UIGenericPart>({
  agentClient,
  children,
}: PropsWithChildren<Props<UIGenericPart>>) {
  const { getRequestSecrets } = useAgentSecrets();
  const [selectedEmbeddingProviders, setSelectedEmbeddingProviders] = useState<Record<string, string>>({});
  const [selectedLLMProviders, setSelectedLLMProviders] = useState<Record<string, string>>({});

  const {
    config: { featureFlags },
  } = useApp();
  const { contextId } = usePlatformContext();

  const { mutateAsync: createContextToken } = useCreateContextToken();

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

  const { data: matchedLLMProviders } = useMatchLLMProviders(
    agentClient?.llmDemands ?? {},
    setDefaultSelectedLLMProviders,
  );

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

  const { data: matchedEmbeddingProviders } = useMatchEmbeddingProviders(
    agentClient?.embeddingDemands ?? {},
    setDefaultSelectedEmbeddingProviders,
  );

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

  const [selectedMCPServers, setSelectedMCPServers] = useState<Record<string, string>>({});

  useEffect(() => {
    setSelectedMCPServers(
      Object.keys(agentClient?.mcpDemands ?? {}).reduce(
        (memo, value) => ({
          ...memo,
          [value]: '',
        }),
        {},
      ),
    );
  }, [agentClient?.mcpDemands]);

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

  const getFullfilments = useCallback(async () => {
    const contextToken = await getContextToken();
    return buildFullfilments({
      contextToken,
      selectedLLMProviders,
      selectedEmbeddingProviders,
      selectedMCPServers,
      requestedSecrets: getRequestSecrets(),
      featureFlags,
    });
  }, [
    getContextToken,
    selectedLLMProviders,
    selectedEmbeddingProviders,
    selectedMCPServers,
    getRequestSecrets,
    featureFlags,
  ]);

  return (
    <AgentDemandsContext.Provider
      value={{
        matchedLLMProviders,
        selectedLLMProviders,
        matchedEmbeddingProviders,
        selectedEmbeddingProviders,
        getFullfilments,
        selectLLMProvider,
        selectEmbeddingProvider,
        selectMCPServer,
        selectedMCPServers,
      }}
    >
      {children}
    </AgentDemandsContext.Provider>
  );
}

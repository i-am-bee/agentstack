/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { type PropsWithChildren, useCallback, useEffect, useRef, useState } from 'react';

import type { AgentA2AClient } from '#api/a2a/types.ts';
import { useApp } from '#contexts/App/index.ts';
import type { Agent } from '#modules/agents/api/types.ts';
import { useAgentSecrets } from '#modules/runs/contexts/agent-secrets/index.ts';

import { useCreateContext } from '../api/mutations/useCreateContext';
import { useCreateContextToken } from '../api/mutations/useCreateContextToken';
import { useMatchEmbeddingProviders, useMatchLLMProviders } from '../api/mutations/useMatchProviders';
import { buildFullfilments } from './build-fulfillments';
import { PlatformContext } from './platform-context';

interface Props<UIGenericPart> {
  agentClient?: AgentA2AClient<UIGenericPart>;
  agent?: Agent;
  contextId?: string;
}

export function PlatformContextProvider<UIGenericPart>({
  agentClient,
  agent,
  contextId: contextIdProp,
  children,
}: PropsWithChildren<Props<UIGenericPart>>) {
  const { getRequestSecrets } = useAgentSecrets();
  const { featureFlags } = useApp();
  const [contextId, setContextId] = useState<string | null>(contextIdProp ?? null);
  const creatingContextRef = useRef(false);

  const [selectedEmbeddingProviders, setSelectedEmbeddingProviders] = useState<Record<string, string>>({});
  const [selectedLLMProviders, setSelectedLLMProviders] = useState<Record<string, string>>({});

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

  const { mutateAsync: createContext } = useCreateContext();
  const { mutateAsync: createContextToken } = useCreateContextToken();
  const { data: matchedLLMProviders } = useMatchLLMProviders(
    agentClient?.llmDemands ?? {},
    setDefaultSelectedLLMProviders,
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

  const setContext = useCallback((context: Awaited<ReturnType<typeof createContext>>) => {
    if (!context) {
      throw new Error(`Context has not been created`);
    }

    setContextId(context.id);
  }, []);

  const resetContext = useCallback(() => {
    setContextId(null);
  }, []);

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
    selectedLLMProviders,
    selectedEmbeddingProviders,
    selectedMCPServers,
    featureFlags,
    getContextToken,
    getRequestSecrets,
  ]);

  useEffect(() => {
    if (contextId || creatingContextRef.current) {
      return;
    }

    creatingContextRef.current = true;

    createContext({
      metadata: {
        agent_name: agent?.name ?? '',
        provider_id: agent?.provider.id ?? '',
      },
    })
      .then(setContext)
      .finally(() => {
        creatingContextRef.current = false;
      });
  }, [contextId, agent, createContext, setContext]);

  const getContextId = useCallback(() => {
    if (!contextId) {
      throw new Error('Context ID is not set');
    }

    return contextId;
  }, [contextId]);

  return (
    <PlatformContext.Provider
      value={{
        contextId,
        matchedLLMProviders,
        selectedLLMProviders,
        matchedEmbeddingProviders,
        selectedEmbeddingProviders,
        getContextId,
        resetContext,
        getContextToken,
        getFullfilments,
        selectLLMProvider,
        selectEmbeddingProvider,
        selectMCPServer,
        selectedMCPServers,
      }}
    >
      {children}
    </PlatformContext.Provider>
  );
}

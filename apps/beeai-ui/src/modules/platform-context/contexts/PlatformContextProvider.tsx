/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { type PropsWithChildren, useCallback, useEffect, useState } from 'react';

import { mcpExtension } from '#api/a2a/extensions/services/mcp.ts';
import { extractServiceExtensionDemands } from '#api/a2a/extensions/utils.ts';
import type { AgentA2AClient } from '#api/a2a/types.ts';
import { useApp } from '#contexts/App/index.ts';

import { useCreateContext } from '../api/mutations/useCreateContext';
import { useCreateContextToken } from '../api/mutations/useCreateContextToken';
import { useMatchProviders } from '../api/mutations/useMatchProviders';
import { buildFullfilments } from './build-fulfillments';
import { PlatformContext } from './platform-context';

interface Props<UIGenericPart> {
  agentClient?: AgentA2AClient<UIGenericPart>;
}

const mcpExtensionExtractor = extractServiceExtensionDemands(mcpExtension);

export function PlatformContextProvider<UIGenericPart>({
  children,
  agentClient,
}: PropsWithChildren<Props<UIGenericPart>>) {
  // TODO: fix
  const mcpDemands = mcpExtensionExtractor(agent?.capabilities.extensions ?? []);

  const { featureFlags } = useApp();
  const [contextId, setContextId] = useState<string | null>(null);
  const [selectedProviders, setSelectedProviders] = useState<Record<string, string>>({});

  const setDefaultSelectedProviders = useCallback(
    (data: Record<string, string[]>) => {
      setSelectedProviders(
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
    [setSelectedProviders],
  );

  const { mutateAsync: createContext } = useCreateContext();
  const { mutateAsync: createContextToken } = useCreateContextToken();
  const { data: matchedProviders } = useMatchProviders(
    agentClient?.llmDemands ? agentClient.llmDemands.llm_demands : {},
    setDefaultSelectedProviders,
  );

  const selectProvider = useCallback(
    (key: string, value: string) => {
      setSelectedProviders((prev) => ({ ...prev, [key]: value }));
    },
    [setSelectedProviders],
  );
  const [selectedMCPServers, setSelectedMCPServers] = useState<Record<string, string>>(
    Object.keys(mcpDemands?.mcp_demands ?? {}).reduce(
      (memo, value) => ({
        ...memo,
        [value]: '',
      }),
      {},
    ),
  );

  const setContext = useCallback(
    (context: Awaited<ReturnType<typeof createContext>>) => {
      if (!context) {
        throw new Error(`Context has not been created`);
      }

      setContextId(context.id);
    },
    [setContextId],
  );

  const resetContext = useCallback(() => {
    setContextId(null);

    createContext().then(setContext);
  }, [createContext, setContext]);

  const selectMCPServer = useCallback(
    (key: string, value: string) => {
      setSelectedMCPServers((prev) => ({ ...prev, [key]: value }));
    },
    [setSelectedMCPServers],
  );

  const getPlatformToken = useCallback(async () => {
    if (contextId === null) {
      throw new Error('Illegal State - Context ID is not set.');
    }

    const contextToken = await createContextToken({
      contextId,
      globalPermissionGrant: {
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
      },
      contextPermissionGrant: {
        files: ['*'],
        vector_stores: ['*'],
      },
    });

    if (!contextToken) {
      throw new Error('Could not generate context token');
    }

    return contextToken.token;
  }, [contextId, createContextToken]);

  const getFullfilments = useCallback(async () => {
    const platformToken = await getPlatformToken();
    return buildFullfilments({ platformToken, selectedProviders, selectedMCPServers, featureFlags });
  }, [getPlatformToken, selectedProviders, selectedMCPServers, featureFlags]);

  useEffect(() => {
    createContext().then(setContext);
  }, [createContext, setContext]);

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
        matchedProviders,
        selectedProviders,
        getContextId,
        resetContext,
        getPlatformToken,
        getFullfilments,
        selectProvider,
        selectMCPServer,
        selectedMCPServers,
      }}
    >
      {children}
    </PlatformContext.Provider>
  );
}

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { type PropsWithChildren, useCallback, useEffect, useState } from 'react';

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

export function PlatformContextProvider<UIGenericPart>({
  children,
  agentClient,
}: PropsWithChildren<Props<UIGenericPart>>) {
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
    return buildFullfilments({ platformToken, selectedProviders, featureFlags });
  }, [getPlatformToken, selectedProviders, featureFlags]);

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
      }}
    >
      {children}
    </PlatformContext.Provider>
  );
}

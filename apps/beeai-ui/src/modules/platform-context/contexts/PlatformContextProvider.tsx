/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { type PropsWithChildren, useCallback, useEffect, useState } from 'react';

import { llmExtension } from '#api/a2a/extensions/services/llm.ts';
import { extractServiceExtensionDemands } from '#api/a2a/extensions/utils.ts';
import type { Agent } from '#modules/agents/api/types.ts';

import { useCreateContext } from '../api/mutations/useCreateContext';
import { useCreateContextToken } from '../api/mutations/useCreateContextToken';
import { useMatchProviders } from '../api/mutations/useMatchProviders';
import { buildFullfilments } from './build-fulfillments';
import { PlatformContext } from './platform-context';

const llmExtensionExtractor = extractServiceExtensionDemands(llmExtension);

export function PlatformContextProvider({ children, agent }: PropsWithChildren<{ agent: Agent | null }>) {
  const llmDemands = llmExtensionExtractor(agent?.capabilities.extensions ?? []);
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
    llmDemands ? llmDemands.llm_demands : {},
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
    return buildFullfilments({ platformToken, selectedProviders });
  }, [getPlatformToken, selectedProviders]);

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
        getContextId,
        resetContext,
        getPlatformToken,
        getFullfilments,
        matchedProviders,
        selectProvider,
      }}
    >
      {children}
    </PlatformContext.Provider>
  );
}

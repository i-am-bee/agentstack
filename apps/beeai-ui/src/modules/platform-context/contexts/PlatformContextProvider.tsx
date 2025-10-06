/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use client';
import { type PropsWithChildren, useCallback, useEffect, useState } from 'react';

import { useParamsFromUrl } from '#hooks/useParamsFromUrl.ts';
import type { Agent } from '#modules/agents/api/types.ts';

import { useCreateContext } from '../api/mutations/useCreateContext';
import type { ListContextHistoryResponse } from '../api/types';
import { PlatformContext } from './platform-context';

interface Props {
  history?: ListContextHistoryResponse;
}

export function PlatformContextProvider({ history, children }: PropsWithChildren<Props>) {
  const { contextId: urlContextId } = useParamsFromUrl();
  const [contextId, setContextId] = useState<string | null>(urlContextId ?? null);

  useEffect(() => {
    setContextId(urlContextId ?? null);
  }, [urlContextId]);

  const { mutateAsync: createContextMutate } = useCreateContext({
    onSuccess: (context) => {
      if (!context) {
        throw new Error(`Context has not been created`);
      }

      setContextId(context.id);
    },
  });

  const resetContext = useCallback(() => {
    setContextId(null);
  }, []);

  const createContext = useCallback(
    async (agent: Agent) => {
      await createContextMutate({
        metadata: {
          agent_name: agent.name ?? '',
          provider_id: agent.provider.id ?? '',
        },
      });
    },
    [createContextMutate],
  );

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
        history,
        createContext,
        getContextId,
        resetContext,
      }}
    >
      {children}
    </PlatformContext.Provider>
  );
}

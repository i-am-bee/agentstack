/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use client';
import { useRouter } from 'next/navigation';
import { type PropsWithChildren, useCallback, useEffect, useState } from 'react';

import type { Agent } from '#modules/agents/api/types.ts';
import { routes } from '#utils/router.ts';

import { useCreateContext } from '../api/mutations/useCreateContext';
import type { ListContextHistoryResponse } from '../api/types';
import { PlatformContext } from './platform-context';

interface Props {
  contextId?: string;
  history?: ListContextHistoryResponse;
}

export function PlatformContextProvider({ contextId: contextIdProp, history, children }: PropsWithChildren<Props>) {
  const [contextId, setContextId] = useState<string | null>(contextIdProp ?? null);

  const router = useRouter();

  useEffect(() => {
    setContextId(contextIdProp ?? null);
  }, [contextIdProp]);

  const { mutateAsync: createContextMutate } = useCreateContext({
    onSuccess: (context) => {
      if (!context) {
        throw new Error(`Context has not been created`);
      }

      setContextId(context.id);
    },
  });

  const resetContext = useCallback(
    (agent: Agent) => {
      if (!contextIdProp) {
        // If contextId is not passed via props, reset it manually.
        // If it is passed, the server already resets it on a new page render,
        // so resetting here would cause a second unnecessary re-creation and possible issues.
        setContextId(null);
      }

      router.push(routes.agentRun({ providerId: agent.provider.id }));
    },
    [contextIdProp, router],
  );

  const createContext = useCallback(
    async (agent: Agent) => {
      createContextMutate({
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
        history: contextId ? history : undefined,
        createContext,
        getContextId,
        resetContext,
      }}
    >
      {children}
    </PlatformContext.Provider>
  );
}

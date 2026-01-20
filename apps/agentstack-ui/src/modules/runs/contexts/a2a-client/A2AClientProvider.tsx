/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';
import type { PropsWithChildren } from 'react';
import { useMemo } from 'react';

import type { Agent } from '#modules/agents/api/types.ts';
import { useContextToken } from '#modules/platform-context/api/queries/useContextToken.ts';
import { useBuildA2AClient } from '#modules/runs/api/queries/useBuildA2AClient.ts';

import { A2AClientContext } from './a2a-client-context';

interface Props {
  agent: Agent;
}

export function A2AClientProvider({ agent, children }: PropsWithChildren<Props>) {
  const { data: contextToken } = useContextToken(agent);
  const { agentClient } = useBuildA2AClient({
    providerId: agent.provider.id,
    authToken: contextToken?.token,
  });

  const contextValue = useMemo(() => {
    if (!agentClient) {
      return null;
    }

    return {
      contextToken,
      agentClient,
    };
  }, [contextToken, agentClient]);

  if (!contextValue) {
    return null;
  }

  return <A2AClientContext.Provider value={contextValue}>{children}</A2AClientContext.Provider>;
}

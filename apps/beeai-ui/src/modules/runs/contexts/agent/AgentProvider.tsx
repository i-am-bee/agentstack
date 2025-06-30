/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { PropsWithChildren } from 'react';
import { useMemo } from 'react';

import type { Agent } from '#modules/agents/api/types.ts';
import { useMonitorProviderStatus } from '#modules/providers/hooks/useMonitorProviderStatus.ts';

import { AgentContext } from './agent-context';

interface Props {
  agent: Agent;
  isMonitorStatusEnabled: boolean;
}

export function AgentProvider({ agent, isMonitorStatusEnabled, children }: PropsWithChildren<Props>) {
  const providerStatus = useMonitorProviderStatus({
    id: agent.metadata.provider_id,
    isEnabled: isMonitorStatusEnabled,
  });

  const contextValue = useMemo(
    () => ({
      agent,
      status: providerStatus,
    }),
    [agent, providerStatus],
  );

  return <AgentContext.Provider value={contextValue}>{children}</AgentContext.Provider>;
}

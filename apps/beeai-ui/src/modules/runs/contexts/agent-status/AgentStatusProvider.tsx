/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { PropsWithChildren } from 'react';
import { useMemo } from 'react';

import type { Agent } from '#modules/agents/api/types.ts';
import { useMonitorProviderStatus } from '#modules/providers/hooks/useMonitorProviderStatus.ts';

import { AgentStatusContext } from './agent-status-context';

interface Props {
  agent: Agent;
  isMonitorStatusEnabled: boolean;
}

export function AgentStatusProvider({ agent, isMonitorStatusEnabled, children }: PropsWithChildren<Props>) {
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

  return <AgentStatusContext.Provider value={contextValue}>{children}</AgentStatusContext.Provider>;
}

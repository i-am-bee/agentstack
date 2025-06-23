/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
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

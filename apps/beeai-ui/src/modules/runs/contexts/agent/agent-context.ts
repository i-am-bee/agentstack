/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { createContext } from 'react';

import type { Agent } from '#modules/agents/api/types.ts';
import type { ProviderStatusWithHelpers } from '#modules/agents/hooks/useProviderStatus.ts';

export const AgentContext = createContext<AgentContextValue | undefined>(undefined);

interface AgentContextValue {
  agent: Agent;
  status: ProviderStatusWithHelpers;
}

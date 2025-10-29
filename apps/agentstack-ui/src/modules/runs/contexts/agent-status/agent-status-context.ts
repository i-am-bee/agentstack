/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use client';

import { createContext } from 'react';

import type { Agent } from '#modules/agents/api/types.ts';
import type { ProviderStatusWithHelpers } from '#modules/agents/hooks/useProviderStatus.ts';

export const AgentStatusContext = createContext<AgentStatusContextValue | undefined>(undefined);

interface AgentStatusContextValue {
  agent: Agent;
  status: ProviderStatusWithHelpers;
}

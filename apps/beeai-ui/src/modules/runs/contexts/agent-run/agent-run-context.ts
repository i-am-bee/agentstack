/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { createContext } from 'react';

import type { Agent } from '#modules/agents/api/types.ts';
import type { RunLog, RunStats } from '#modules/runs/types.ts';

export const AgentRunContext = createContext<AgentRunContextValue | undefined>(undefined);

interface AgentRunContextValue {
  agent: Agent;
  isPending: boolean;
  input?: string;
  stats?: RunStats;
  logs?: RunLog[];
  run: (input: string) => Promise<void>;
  cancel: () => void;
  clear: () => void;
}

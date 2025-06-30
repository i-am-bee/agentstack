/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { createContext } from 'react';

import type { Agent } from '#modules/agents/api/types.ts';
import type { RunLog, RunStats } from '#modules/runs/types.ts';

export const HandsOffContext = createContext<HandsOffContextValue | undefined>(undefined);

interface HandsOffContextValue {
  agent: Agent;
  input?: string;
  stats?: RunStats;
  logs?: RunLog[];
  output?: string;
  isPending: boolean;
  onSubmit: (input: string) => Promise<void>;
  onClear: () => void;
}

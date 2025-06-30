/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { createContext } from 'react';
import type { UseFieldArrayReturn } from 'react-hook-form';

import type { Agent } from '#modules/agents/api/types.ts';
import type { RunStats } from '#modules/runs/types.ts';

export const ComposeContext = createContext<ComposeContextValue | null>(null);

export enum ComposeStatus {
  Ready = 'ready',
  InProgress = 'in-progress',
  Completed = 'completed',
}
interface ComposeContextValue {
  result?: string;
  status: ComposeStatus;
  stepsFields: UseFieldArrayReturn<SequentialFormValues, 'steps'>;
  onSubmit: () => void;
  onCancel: () => void;
  onReset: () => void;
}

export interface ComposeStep {
  agent: Agent;
  instruction: string;
  result?: string;
  isPending?: boolean;
  logs?: string[];
  stats?: RunStats;
}

export interface SequentialFormValues {
  steps: ComposeStep[];
}

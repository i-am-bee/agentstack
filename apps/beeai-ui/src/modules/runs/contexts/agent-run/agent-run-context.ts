/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use client';
import { createContext } from 'react';

import type { AgentA2AClient } from '#api/a2a/types.ts';
import type { Agent } from '#modules/agents/api/types.ts';
import type { UIMessageForm } from '#modules/messages/types.ts';
import type { RunStats } from '#modules/runs/types.ts';
import type { TaskId } from '#modules/tasks/api/types.ts';

import type { FullfillmentsContext } from '../agent-demands/agent-demands-context';

export const AgentRunContext = createContext<AgentRunContextValue | undefined>(undefined);

interface AgentRunContextValue {
  agent: Agent;
  agentClient?: AgentA2AClient;
  status: AgentRunStatus;
  isPending: boolean;
  isInitializing: boolean;
  isReady: boolean;
  input?: string;
  stats?: RunStats;
  hasMessages: boolean;
  chat: (input: string, fullfillmentsContext: FullfillmentsContext) => Promise<void>;
  submitForm: (form: UIMessageForm) => Promise<void>;
  submitRuntimeForm: (form: UIMessageForm, taskId: TaskId) => Promise<void>;
  startAuth: (url: string, taskId: TaskId) => void;
  submitSecrets: (taskId: TaskId, secrets: Record<string, string>) => Promise<void>;
  cancel: () => void;
  clear: () => void;
}

export enum AgentRunStatus {
  Initializing = 'initializing',
  Ready = 'ready',
  Pending = 'pending',
}

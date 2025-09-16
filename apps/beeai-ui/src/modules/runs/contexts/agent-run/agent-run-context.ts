/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use client';
import { createContext } from 'react';

import type { AgentSettings, SettingsRender } from '#api/a2a/extensions/ui/settings.ts';
import type { Agent } from '#modules/agents/api/types.ts';
import type { UIMessageForm } from '#modules/messages/types.ts';
import type { RunStats } from '#modules/runs/types.ts';
import type { TaskId } from '#modules/tasks/api/types.ts';

export const AgentRunContext = createContext<AgentRunContextValue | undefined>(undefined);

interface AgentRunContextValue {
  agent: Agent;
  status: AgentRunStatus;
  isPending: boolean;
  isInitializing: boolean;
  isActionRequired: boolean;
  isReady: boolean;
  input?: string;
  stats?: RunStats;
  hasMessages: boolean;
  settingsRender: SettingsRender | null;
  chat: (input: string) => Promise<void>;
  submitForm: (form: UIMessageForm, taskId?: string) => Promise<void>;
  startAuth: (url: string, taskId: TaskId) => void;
  cancel: () => void;
  clear: () => void;
  onUpdateSettings: (values: AgentSettings) => void;
  getSettings: () => AgentSettings | undefined;
}

export enum AgentRunStatus {
  Initializing = 'initializing',
  Ready = 'ready',
  Pending = 'pending',
  ActionRequired = 'action-required',
}

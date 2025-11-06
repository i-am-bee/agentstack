/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { AgentSettings, FormFulfillments, Fulfillments, SettingsDemands } from 'agentstack-sdk';
import { createContext } from 'react';

import type { TaskId } from '#modules/tasks/api/types.ts';
import { RunFormValues } from '#modules/form/types.ts';
import { UIMessageForm } from '#modules/messages/types.ts';

export type FulfillmentsContext = Partial<{
  taskId: TaskId;
  providedSecrets: Record<string, string>;
  oauthRedirectUri: string;
  form: UIMessageForm;
}>;

interface AgentDemandsContextValue {
  matchedLLMProviders?: Record<string, string[]>;
  selectedLLMProviders: Record<string, string>;
  matchedEmbeddingProviders?: Record<string, string[]>;
  selectedEmbeddingProviders: Record<string, string>;
  getFulfillments: (context: FulfillmentsContext) => Promise<Fulfillments>;
  selectLLMProvider: (key: string, value: string) => void;
  selectEmbeddingProvider: (key: string, value: string) => void;
  selectMCPServer: (key: string, value: string) => void;
  provideFormValues: (values: RunFormValues) => void;
  selectedMCPServers: Record<string, string>;

  onUpdateSettings: (settings: AgentSettings) => void;
  selectedSettings: AgentSettings | undefined;
  settingsDemands: SettingsDemands | null;
}

export const AgentDemandsContext = createContext<AgentDemandsContextValue | null>(null);

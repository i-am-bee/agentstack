/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type {
  ApprovalDecision,
  FormDemands,
  Fulfillments,
  SettingsFormRender,
  SettingsFormValues,
} from 'agentstack-sdk';
import { createContext } from 'react';

import type { RunFormValues } from '#modules/form/types.ts';
import type { UIMessageForm } from '#modules/messages/types.ts';
import type { TaskId } from '#modules/tasks/api/types.ts';

export type FulfillmentsContext = Partial<{
  taskId: TaskId;
  providedSecrets: Record<string, string>;
  oauthRedirectUri: string;
  approvalDecision: ApprovalDecision;
  form: UIMessageForm;
}>;

export interface ModelProvidersContextValue {
  isEnabled: boolean;
  isLoading: boolean;
  matched?: Record<string, string[]>;
  selected: Record<string, string>;
  select: (key: string, value: string) => void;
}

export type ProvideFormValuesParams = {
  formId: 'initial_form' | 'settings_form';
  values: RunFormValues;
};

interface AgentDemandsContextValue {
  llmProviders: ModelProvidersContextValue;
  embeddingProviders: ModelProvidersContextValue;
  formDemands: FormDemands | null;
  settingsForm: SettingsFormRender | null;
  selectedSettings: SettingsFormValues | undefined;
  getFulfillments: (context: FulfillmentsContext) => Promise<Fulfillments>;
  provideFormValues: ({ formId, values }: ProvideFormValuesParams) => void;
  onUpdateSettings: (settings: SettingsFormValues) => void;
}

export const AgentDemandsContext = createContext<AgentDemandsContextValue | null>(null);

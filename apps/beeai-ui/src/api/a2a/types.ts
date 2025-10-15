/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type {
  AgentSettings,
  ContextToken,
  EmbeddingDemands,
  EmbeddingFulfillments,
  FormRender,
  LLMDemands,
  LLMFulfillments,
  MCPDemand,
  MCPFulfillment,
  OAuthDemand,
  OAuthFulfillment,
  SecretDemands,
  SecretFulfillment,
} from 'beeai-sdk';

import type { UIMessagePart, UIUserMessage } from '#modules/messages/types.ts';
import type { AgentRequestSecrets } from '#modules/runs/contexts/agent-secrets/types.ts';
import type { ContextId, TaskId } from '#modules/tasks/api/types.ts';

import type { buildA2AClient } from './client';

export enum RunResultType {
  FormRequired = 'form-required',
  OAuthRequired = 'oauth-required',
  SecretRequired = 'secret-required',
  Parts = 'parts',
}

export interface FormRequiredResult {
  type: RunResultType.FormRequired;
  taskId: TaskId;
  form: FormRender;
}

export interface OAuthRequiredResult {
  type: RunResultType.OAuthRequired;
  taskId: TaskId;
  url: string;
}

export interface SecretRequiredResult {
  type: RunResultType.SecretRequired;
  taskId: TaskId;
  secret: SecretDemands;
}

export interface PartsResult<UIGenericPart = never> {
  type: RunResultType.Parts;
  taskId: TaskId;
  parts: Array<UIMessagePart | UIGenericPart>;
}

export type ChatResult<UIGenericPart = never> =
  | PartsResult<UIGenericPart>
  | FormRequiredResult
  | OAuthRequiredResult
  | SecretRequiredResult;

export interface ChatParams {
  message: UIUserMessage;
  contextId: ContextId;
  fulfillments: Fulfillments;
  settings?: AgentSettings;
  taskId?: TaskId;
}

export interface ChatRun<UIGenericPart = never> {
  taskId?: TaskId;
  done: Promise<null | FormRequiredResult | OAuthRequiredResult | SecretRequiredResult>;
  subscribe: (fn: (data: { parts: (UIMessagePart | UIGenericPart)[]; taskId: TaskId }) => void) => () => void;
  cancel: () => Promise<void>;
}

export interface Fulfillments {
  mcp: (demand: MCPDemand) => Promise<MCPFulfillment | null>;
  llm: (demand: LLMDemands) => Promise<LLMFulfillments>;
  oauth: (demand: OAuthDemand) => Promise<OAuthFulfillment | null>;
  getContextToken: () => ContextToken;
  embedding: (demand: EmbeddingDemands) => Promise<EmbeddingFulfillments>;
  secrets: (demand: SecretDemands, runtimeFullfilledDemands?: AgentRequestSecrets) => Promise<SecretFulfillment>;
}

export type AgentA2AClient<UIGenericPart = never> = Awaited<ReturnType<typeof buildA2AClient<UIGenericPart>>>;

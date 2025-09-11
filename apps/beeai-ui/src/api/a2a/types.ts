/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { UIMessagePart, UIUserMessage } from '#modules/messages/types.ts';
import type { ContextId, TaskId } from '#modules/tasks/api/types.ts';

import type { buildA2AClient } from './client';
import type { LLMDemand, LLMFulfillment } from './extensions/services/llm';
import type { MCPDemand, MCPFulfillment } from './extensions/services/mcp';
import type { OAuthDemand, OAuthFulfillment } from './extensions/services/oauth-provider';
import type { FormRender } from './extensions/ui/form';
import type { AgentSettings } from './extensions/ui/settings';

export enum RunResultType {
  FormRequired = 'form-required',
  AuthRequired = 'auth-required',
  Parts = 'parts',
}

export interface FormRequiredResult {
  type: RunResultType.FormRequired;
  taskId: TaskId;
  form: FormRender;
}

export interface AuthRequiredResult {
  type: RunResultType.AuthRequired;
  taskId: TaskId;
  url: string;
}

export interface PartsResult<UIGenericPart = never> {
  type: RunResultType.Parts;
  taskId: TaskId;
  parts: Array<UIMessagePart | UIGenericPart>;
}

export type ChatResult<UIGenericPart = never> = PartsResult<UIGenericPart> | FormRequiredResult | AuthRequiredResult;

export interface ChatParams {
  message: UIUserMessage;
  contextId: ContextId;
  fulfillments: Fulfillments;
  settings?: AgentSettings;
  taskId?: TaskId;
}

export interface ChatRun<UIGenericPart = never> {
  taskId?: TaskId;
  done: Promise<null | FormRequiredResult | AuthRequiredResult>;
  subscribe: (fn: (data: { parts: (UIMessagePart | UIGenericPart)[]; taskId: TaskId }) => void) => () => void;
  cancel: () => Promise<void>;
}

export interface Fulfillments {
  mcp: (demand: MCPDemand) => Promise<MCPFulfillment | null>;
  llm: (demand: LLMDemand) => Promise<LLMFulfillment>;
  oauth: (demand: OAuthDemand) => Promise<OAuthFulfillment | null>;
}

export type AgentA2AClient<UIGenericPart = never> = Awaited<ReturnType<typeof buildA2AClient<UIGenericPart>>>;

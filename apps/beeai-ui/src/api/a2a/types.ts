/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { UIMessagePart, UIUserMessage } from '#modules/messages/types.ts';
import type { ContextId, TaskId } from '#modules/tasks/api/types.ts';

import type { LLMDemand, LLMFulfillment } from './extensions/services/llm';
import type { MCPDemand, MCPFulfillment } from './extensions/services/mcp';
import type { FormRender } from './extensions/ui/form';

export enum RunResultType {
  FormRequired = 'form-required',
  Parts = 'parts',
}

export interface FormRequiredResult {
  type: RunResultType.FormRequired;
  taskId: TaskId;
  form: FormRender;
}

export interface PartsResult<UIGenericPart = never> {
  type: RunResultType.Parts;
  taskId: TaskId;
  parts: Array<UIMessagePart | UIGenericPart>;
}

export type ChatResult<UIGenericPart = never> = PartsResult<UIGenericPart> | FormRequiredResult;

export interface ChatParams {
  message: UIUserMessage;
  contextId: ContextId;
  fulfillments: Fulfillments;
  taskId?: TaskId;
}

export interface ChatRun<UIGenericPart = never> {
  taskId?: TaskId;
  done: Promise<null | FormRequiredResult>;
  subscribe: (fn: (data: { parts: (UIMessagePart | UIGenericPart)[]; taskId: TaskId }) => void) => () => void;
  cancel: () => Promise<void>;
}

export interface Fulfillments {
  mcp: (demand: MCPDemand) => Promise<MCPFulfillment>;
  llm: (demand: LLMDemand) => Promise<LLMFulfillment>;
}

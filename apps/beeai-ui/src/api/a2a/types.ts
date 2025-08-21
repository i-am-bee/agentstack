/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { UIMessagePart, UIUserMessage } from '#modules/messages/types.ts';
import type { ContextId, TaskId } from '#modules/tasks/api/types.ts';

import type { LLMDemand, LLMFulfillment } from './extensions/services/llm';
import type { MCPDemand, MCPFulfillment } from './extensions/services/mcp';
import type { FormRender, FormResponse } from './extensions/ui/form';

export enum UnfinishedTaskResult {
  FormRequired = 'form-required',
}

export interface FormRequired {
  taskId: TaskId;
  type: UnfinishedTaskResult.FormRequired;
  form: FormRender;
}

export interface ChatParams {
  message: UIUserMessage;
  contextId: ContextId;
  fulfillments: Fulfillments;
  taskId?: TaskId;
  formResponse?: FormResponse;
}

export interface ChatRun<UIGenericPart = never> {
  done: Promise<null | FormRequired>;
  subscribe: (fn: (data: { parts: (UIMessagePart | UIGenericPart)[]; taskId: TaskId }) => void) => () => void;
  cancel: () => Promise<void>;
}

export interface Fulfillments {
  mcp: (demand: MCPDemand) => Promise<MCPFulfillment>;
  llm: (demand: LLMDemand) => Promise<LLMFulfillment>;
}

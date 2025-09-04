/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { UIMessagePart, UIUserMessage } from '#modules/messages/types.ts';
import type { ContextId, TaskId } from '#modules/tasks/api/types.ts';

import type { buildA2AClient } from './client';
import type { LLMDemand, LLMFulfillment } from './extensions/services/llm';
import type { MCPDemand, MCPFulfillment } from './extensions/services/mcp';

export interface ChatParams {
  message: UIUserMessage;
  contextId: ContextId;
  fulfillments: Fulfillments;
}

export interface ChatRun<UIGenericPart = never> {
  done: Promise<void>;
  subscribe: (fn: (data: { parts: (UIMessagePart | UIGenericPart)[]; taskId: TaskId }) => void) => () => void;
  cancel: () => Promise<void>;
}

export interface Fulfillments {
  mcp: (demand: MCPDemand) => Promise<MCPFulfillment>;
  llm: (demand: LLMDemand) => Promise<LLMFulfillment>;
}

export type AgentA2AClient<UIGenericPart = never> = ReturnType<typeof buildA2AClient<UIGenericPart>>;

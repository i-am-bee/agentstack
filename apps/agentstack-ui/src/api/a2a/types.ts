/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Fulfillments, InputRequiredResponses, TaskStatusUpdateResult } from 'agentstack-sdk';

import type { UIMessagePart, UIUserMessage } from '#modules/messages/types.ts';
import type { ContextId, TaskId } from '#modules/tasks/api/types.ts';

import type { buildA2AClient } from './client';

export enum RunResultType {
  Parts = 'parts',
}

export interface PartsResult<UIGenericPart = never> {
  type: RunResultType.Parts;
  taskId: TaskId;
  parts: Array<UIMessagePart | UIGenericPart>;
}

export type TaskStatusUpdateResultWithTaskId = TaskStatusUpdateResult & {
  taskId: TaskId;
};

export type ChatResult<UIGenericPart = never> = PartsResult<UIGenericPart> | TaskStatusUpdateResultWithTaskId;

export interface ChatParams {
  message: UIUserMessage;
  contextId: ContextId;
  fulfillments: Fulfillments;
  responses: InputRequiredResponses;
  taskId?: TaskId;
}

export interface ChatRun<UIGenericPart = never> {
  taskId?: TaskId;
  done: Promise<null | TaskStatusUpdateResultWithTaskId>;
  subscribe: (fn: (data: { parts: (UIMessagePart | UIGenericPart)[]; taskId: TaskId }) => void) => () => void;
  cancel: () => Promise<void>;
}

export type AgentA2AClient<UIGenericPart = never> = Awaited<ReturnType<typeof buildA2AClient<UIGenericPart>>>;

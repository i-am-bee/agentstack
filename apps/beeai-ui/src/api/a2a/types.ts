/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { TaskStatusUpdateEvent } from '@a2a-js/sdk';

import type { UIMessagePart } from '#modules/messages/types.ts';
import type { TaskId } from '#modules/tasks/api/types.ts';

export interface ChatRun<UIGenericPart = never> {
  done: Promise<void>;
  subscribe: (fn: (data: { parts: (UIMessagePart | UIGenericPart)[]; taskId: TaskId }) => void) => () => void;
  cancel: () => Promise<void>;
}

export type A2AClientStatusUpdateHandlerParams = {
  event: TaskStatusUpdateEvent;
  nativeHandler: (event: TaskStatusUpdateEvent) => UIMessagePart[];
};

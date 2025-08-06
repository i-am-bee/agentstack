/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { UIMessagePart } from '#modules/messages/types.ts';
import type { TaskId } from '#modules/tasks/api/types.ts';

export interface ChatRun<UIGenericPart = never> {
  done: Promise<void>;
  subscribe: (fn: (data: { parts: (UIMessagePart | UIGenericPart)[]; taskId: TaskId }) => void) => () => void;
  cancel: () => Promise<void>;
}

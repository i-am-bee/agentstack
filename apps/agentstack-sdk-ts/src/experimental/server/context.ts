/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Task } from '@a2a-js/sdk';

export class RunContext {
  public readonly taskId: string;
  public readonly contextId: string;
  public readonly task?: Task;

  constructor(taskId: string, contextId: string, task?: Task) {
    this.taskId = taskId;
    this.contextId = contextId;
    this.task = task;
  }
}

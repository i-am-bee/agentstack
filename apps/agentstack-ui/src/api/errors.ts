/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { isHttpError } from 'agentstack-sdk';

import type { A2AErrorMetadata } from './types';

export class UnauthenticatedError extends Error {
  name: string;
  response?: Response;

  constructor({ message, response }: { message?: string; response?: Response }) {
    super(message);

    this.name = new.target.name;
    this.response = response;

    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class A2AExtensionError extends Error {
  error: A2AErrorMetadata['error'];
  context: A2AErrorMetadata['context'];
  stackTrace: A2AErrorMetadata['stack_trace'];

  constructor({ error, context, stack_trace }: A2AErrorMetadata) {
    super(error.message);

    this.error = error;
    this.context = context;
    this.stackTrace = stack_trace;
  }
}

export class TaskCanceledError extends Error {
  taskId?: string;

  constructor(taskId?: string) {
    super('The task timed out or was canceled.');
    this.taskId = taskId;
  }
}

export function isUnauthenticatedError(error: unknown) {
  return error instanceof UnauthenticatedError || isHttpError(error, 401);
}

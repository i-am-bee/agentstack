/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type {
  A2AErrorMetadata,
  ApiErrorCode,
  ApiErrorResponse,
  ApiValidationErrorResponse,
  StreamErrorResponse,
} from './types';

export class ErrorWithResponse extends Error {
  name: string;
  response?: Response;

  constructor({ message, response }: { message?: string; response?: Response }) {
    super(message);

    this.name = new.target.name;
    this.response = response;

    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class ApiError extends ErrorWithResponse {
  error: ApiErrorResponse;
  code: ApiErrorCode;

  constructor({ error, response }: { error: ApiErrorResponse; response?: Response }) {
    super({ message: error.message, response });

    this.error = error;
    this.code = error.code;
  }
}

export class HttpError extends ErrorWithResponse {
  code: number;

  constructor({ message, response }: { message?: string; response: Response }) {
    super({ message, response });

    this.code = response.status;
  }
}

export class ApiValidationError extends ErrorWithResponse {
  error: ApiValidationErrorResponse;

  constructor({ error, response }: { error: ApiValidationErrorResponse; response?: Response }) {
    super({ message: JSON.stringify(error.detail), response });

    this.error = error;
  }
}

export class StreamError extends ErrorWithResponse {
  error: StreamErrorResponse;
  code: StreamErrorResponse['status_code'];

  constructor({ error, response }: { error: StreamErrorResponse; response?: Response }) {
    super({ message: error.detail, response });

    this.error = error;
    this.code = error.status_code;
  }
}

export class UnauthenticatedError extends ErrorWithResponse {}

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

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { HttpError, NetworkError, ParseError, ValidationError } from './types';
import { type ApiError, ApiErrorType } from './types';

export class ApiErrorException extends Error {
  apiError: ApiError;

  constructor(apiError: ApiError) {
    super(apiError.message);

    this.apiError = apiError;
  }
}

export function isApiError(error: unknown): error is ApiErrorException {
  return error instanceof ApiErrorException;
}

export function isHttpError(error: unknown, status?: number): error is ApiErrorException & { apiError: HttpError } {
  if (!isApiError(error)) {
    return false;
  }

  const { apiError } = error;

  if (apiError.type !== ApiErrorType.Http) {
    return false;
  }

  if (typeof status === 'number') {
    return apiError.response.status === status;
  }

  return true;
}

export function isNetworkError(error: unknown): error is ApiErrorException & { apiError: NetworkError } {
  if (!isApiError(error)) {
    return false;
  }

  return error.apiError.type === ApiErrorType.Network;
}

export function isParseError(error: unknown): error is ApiErrorException & { apiError: ParseError } {
  if (!isApiError(error)) {
    return false;
  }

  return error.apiError.type === ApiErrorType.Parse;
}

export function isValidationError(error: unknown): error is ApiErrorException & { apiError: ValidationError } {
  if (!isApiError(error)) {
    return false;
  }

  return error.apiError.type === ApiErrorType.Validation;
}

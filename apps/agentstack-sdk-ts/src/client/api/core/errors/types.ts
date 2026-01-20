/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ZodError } from 'zod';

import type { ApiRequest, ApiResponse } from '../types';

export enum ApiErrorType {
  Http = 'http',
  Network = 'network',
  Parse = 'parse',
  Unknown = 'unknown',
  Validation = 'validation',
}

export interface ApiErrorBase {
  message: string;
  request: ApiRequest;
}

export interface HttpError extends ApiErrorBase {
  type: ApiErrorType.Http;
  response: ApiResponse;
}

export interface NetworkError extends ApiErrorBase {
  type: ApiErrorType.Network;
  details: unknown;
}

export interface ParseError extends ApiErrorBase {
  type: ApiErrorType.Parse;
  response: ApiResponse;
  details: Error;
}

export interface ValidationError extends ApiErrorBase {
  type: ApiErrorType.Validation;
  response: ApiResponse;
  details: ZodError;
}

export type ApiError = HttpError | NetworkError | ParseError | ValidationError;

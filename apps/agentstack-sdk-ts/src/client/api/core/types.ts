/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type z from 'zod';

import type { buildApiClient } from './client';
import type { ApiError } from './errors';

export enum ApiMethod {
  Get = 'GET',
  Post = 'POST',
  Put = 'PUT',
  Delete = 'DELETE',
  Patch = 'PATCH',
}

export type ApiQueryParams = Record<string, unknown>;
export type ApiRequestBody = Record<string, unknown> | FormData;

export interface ApiParams<T> {
  method: ApiMethod;
  path: string;
  schema: z.ZodSchema<T>;
  query?: ApiQueryParams;
  body?: ApiRequestBody;
  parseAsStream?: boolean;
}

export interface ApiRequest {
  method: ApiMethod;
  url: string;
}

export interface ApiResponse {
  status: number;
  statusText: string;
  bodyText: ReadableStream<Uint8Array> | string | null;
}

export interface ApiSuccess<T> {
  ok: true;
  data: T;
  response: ApiResponse;
}

export interface ApiFailure {
  ok: false;
  error: ApiError;
}

export type ApiResult<T> = ApiSuccess<T> | ApiFailure;

export type CallApi = <T>(params: ApiParams<T>) => Promise<ApiResult<T>>;

export type AgentStackClient = ReturnType<typeof buildApiClient>;

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { components } from './schema';

export type ApiErrorResponse = components['schemas']['Error'];

export type ApiErrorCode = ApiErrorResponse['code'];

export type AcpErrorResponse = { error: ApiErrorResponse };

export type ApiValidationErrorResponse = components['schemas']['HTTPValidationError'];

export type HttpErrorResponse = {
  detail?: string;
};

export type StreamErrorResponse = {
  status_code: number;
  type: string;
  detail: string;
};

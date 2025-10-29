/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ApiErrorCode, ApiErrorResponse } from './types';

export function createApiErrorResponse(code: ApiErrorCode, message?: string): ApiErrorResponse {
  return {
    code,
    message: message ?? 'Error',
  };
}

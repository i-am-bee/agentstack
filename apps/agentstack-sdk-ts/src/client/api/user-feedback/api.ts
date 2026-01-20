/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { CallApi } from '../core/types';
import { ApiMethod } from '../core/types';
import { createUserFeedbackResponseSchema } from './schemas';
import type { CreateUserFeedbackRequest } from './types';

export function createUserFeedbackApi(callApi: CallApi) {
  const createUserFeedback = ({ ...body }: CreateUserFeedbackRequest) =>
    callApi({
      method: ApiMethod.Post,
      path: '/api/v1/user_feedback',
      schema: createUserFeedbackResponseSchema,
      body,
    });

  return {
    createUserFeedback,
  };
}

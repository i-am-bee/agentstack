/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { api } from '#api/index.ts';
import { ensureData } from '#api/utils.ts';

import type { SendFeedbackRequest } from './types';

export async function sendFeedback(body: SendFeedbackRequest) {
  const response = await api.POST('/api/v1/user_feedback', { body });

  return ensureData(response);
}

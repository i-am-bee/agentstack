/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { type CreateUserFeedbackRequest, unwrapResult } from 'agentstack-sdk';

import { agentStackClient } from '#api/agentstack-client.ts';

export async function sendFeedback(request: CreateUserFeedbackRequest) {
  const response = await agentStackClient.createUserFeedback(request);
  const result = unwrapResult(response);

  return result;
}

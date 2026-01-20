/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { UpdateVariablesRequest } from 'agentstack-sdk';
import { unwrapResult } from 'agentstack-sdk';

import { agentStackClient } from '#api/agentstack-client.ts';

export async function listVariables() {
  const response = await agentStackClient.listVariables();
  const result = unwrapResult(response);

  return result;
}

export async function updateVariables(request: UpdateVariablesRequest) {
  const response = await agentStackClient.updateVariables(request);
  const result = unwrapResult(response);

  return result;
}

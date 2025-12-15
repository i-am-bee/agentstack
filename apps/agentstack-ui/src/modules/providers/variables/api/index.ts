/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ListProviderVariablesRequest, UpdateProviderVariablesRequest } from 'agentstack-sdk';
import { unwrapResult } from 'agentstack-sdk';

import { agentStackClient } from '#api/agentstack-client.ts';

import type { DeleteProviderVariableRequest } from './types';

export async function listProviderVariables(request: ListProviderVariablesRequest) {
  const response = await agentStackClient.listProviderVariables(request);
  const result = unwrapResult(response);

  return result;
}

export async function updateProviderVariables(request: UpdateProviderVariablesRequest) {
  const response = await agentStackClient.updateProviderVariables(request);
  const result = unwrapResult(response);

  return result;
}

export async function deleteProviderVariable({ name, ...request }: DeleteProviderVariableRequest) {
  const response = await agentStackClient.updateProviderVariables({ ...request, variables: { [name]: null } });
  const result = unwrapResult(response);

  return result;
}

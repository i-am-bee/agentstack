/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { api } from '#api/index.ts';
import { ensureData } from '#api/utils.ts';

import type { DeleteVariableParams, ListVariablesPath, UpdateVariableParams } from './types';

export async function listVariables(path: ListVariablesPath) {
  const response = await api.GET('/api/v1/providers/{id}/variables', { params: { path } });

  return ensureData(response);
}

export async function updateVariable({ id, variables }: UpdateVariableParams) {
  const response = await api.PUT('/api/v1/providers/{id}/variables', {
    params: { path: { id } },
    body: { variables },
  });

  return ensureData(response);
}

export async function deleteVariable({ id, name }: DeleteVariableParams) {
  const response = await api.PUT('/api/v1/providers/{id}/variables', {
    params: { path: { id } },
    body: { variables: { [name]: null } },
  });

  return ensureData(response);
}

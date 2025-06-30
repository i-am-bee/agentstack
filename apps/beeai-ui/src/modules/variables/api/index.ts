/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { api } from '#api/index.ts';
import { ensureData } from '#api/utils.ts';

import type { UpdateVariablesRequest } from './types';

export async function listVariables() {
  const response = await api.GET('/api/v1/variables');

  return ensureData(response);
}

export async function updateVariable({ body }: { body: UpdateVariablesRequest['env'] }) {
  const response = await api.PUT('/api/v1/variables', { body: { env: body } });

  return ensureData(response);
}

export async function deleteVariable({ name }: { name: string }) {
  const response = await api.PUT('/api/v1/variables', { body: { env: { [name]: null } } });

  return ensureData(response);
}

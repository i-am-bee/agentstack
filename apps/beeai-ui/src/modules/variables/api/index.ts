/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { api } from '#api/index.ts';
import { ensureData } from '#api/utils.ts';

import type { UpdateVariablesParams } from './types';

export async function listVariables() {
  const response = await api.GET('/api/v1/variables');

  return ensureData(response);
}

export async function updateVariable({ variables }: UpdateVariablesParams) {
  const response = await api.PUT('/api/v1/variables', {
    body: { variables },
  });

  return ensureData(response);
}

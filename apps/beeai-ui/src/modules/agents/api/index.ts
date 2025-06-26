/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { api } from '#api/index.ts';
import { ensureData } from '#api/utils.ts';

import type { ReadAgentPath } from './types';

export async function listAgents() {
  const response = await api.GET('/api/v1/acp/agents');

  return ensureData(response);
}

export async function readAgent({ name }: ReadAgentPath) {
  const response = await api.GET('/api/v1/acp/agents/{name}', { params: { path: { name } } });

  return ensureData(response);
}

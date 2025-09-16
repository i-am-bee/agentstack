/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { api } from '#api/index.ts';
import { ensureData } from '#api/utils.ts';

import type { ListContextHistoryParams, ListContextsParams } from '../types';
import type { CreateContextTokenParams, MatchModelProvidersParams } from './types';

export async function createContext() {
  const response = await api.POST('/api/v1/contexts', { body: {} });

  return ensureData(response);
}

export async function listContexts({ query }: ListContextsParams) {
  const response = await api.GET('/api/v1/contexts', { params: { query } });

  return ensureData(response);
}

export async function listContextHistory({ contextId, query }: ListContextHistoryParams) {
  const response = await api.GET('/api/v1/contexts/{context_id}/history', {
    params: { path: { context_id: contextId }, query },
  });

  return ensureData(response);
}

export async function matchProviders({ capability, suggested_models }: MatchModelProvidersParams) {
  const response = await api.POST('/api/v1/model_providers/match', {
    body: { capability, score_cutoff: 0.4, suggested_models },
  });

  return ensureData(response);
}

export async function createContextToken({
  context_id,
  grant_context_permissions,
  grant_global_permissions,
}: CreateContextTokenParams) {
  const response = await api.POST('/api/v1/contexts/{context_id}/token', {
    body: { grant_context_permissions, grant_global_permissions },
    params: { path: { context_id } },
  });

  return ensureData(response);
}

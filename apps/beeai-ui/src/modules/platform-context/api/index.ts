/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { api } from '#api/index.ts';
import { ensureData, fetchEntity } from '#api/utils.ts';

import type {
  CreateContextParams,
  CreateContextTokenParams,
  DeleteContextParams,
  ListContextHistoryParams,
  ListContextsParams,
  MatchModelProvidersParams,
} from './types';

export async function createContext(body: CreateContextParams) {
  const response = await api.POST('/api/v1/contexts', { body });

  return ensureData(response);
}

export async function listContexts({ query }: ListContextsParams) {
  const response = await api.GET('/api/v1/contexts', { params: { query } });

  return ensureData(response);
}

export async function deleteContext({ context_id }: DeleteContextParams) {
  const response = await api.DELETE('/api/v1/contexts/{context_id}', { params: { path: { context_id } } });

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

export async function fetchContextHistory(params: ListContextHistoryParams) {
  return await fetchEntity(() => listContextHistory(params));
}

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { agentstackClient } from '#api/agentstack-client.ts';
import { api } from '#api/index.ts';
import { ensureData, fetchEntity } from '#api/utils.ts';

import type {
  CreateContextParams,
  CreateContextTokenParams,
  DeleteContextParams,
  ListContextHistoryParams,
  ListContextsParams,
  MatchModelProvidersParams,
  UpdateContextMetadataParams,
} from './types';

export async function createContext(body: CreateContextParams) {
  const context = await agentstackClient.createContext(body.provider_id ?? '');
  return {
    ...context,
    metadata: context.metadata as { [key: string]: string } | null | undefined,
  };
}

export async function listContexts(params: ListContextsParams) {
  const response = await api.GET('/api/v1/contexts', { params });

  return ensureData(response);
}

export async function updateContextMetadata({ context_id, metadata }: UpdateContextMetadataParams) {
  const response = await api.PATCH('/api/v1/contexts/{context_id}/metadata', {
    body: { metadata },
    params: { path: { context_id } },
  });

  return ensureData(response);
}

export async function deleteContext(path: DeleteContextParams) {
  const response = await api.DELETE('/api/v1/contexts/{context_id}', { params: { path } });

  return ensureData(response);
}

export async function listContextHistory({ contextId, query }: ListContextHistoryParams) {
  const response = await api.GET('/api/v1/contexts/{context_id}/history', {
    params: { path: { context_id: contextId }, query },
  });

  return ensureData(response);
}

export async function matchProviders({ capability, suggested_models }: MatchModelProvidersParams) {
  return await agentstackClient.matchProviders({
    suggestedModels: suggested_models ?? null,
    capability,
    scoreCutoff: 0.4,
  });
}

export async function createContextToken({
  context_id,
  grant_context_permissions,
  grant_global_permissions,
}: CreateContextTokenParams) {
  const result = await agentstackClient.createContextToken({
    contextId: context_id,
    globalPermissions: grant_global_permissions ?? {},
    contextPermissions: grant_context_permissions ?? {},
  });
  return result.token;
}

export async function fetchContextHistory(params: ListContextHistoryParams) {
  return await fetchEntity(() => listContextHistory(params));
}

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { CreateContextResponse, CreateContextTokenParams, MatchProvidersParams } from 'agentstack-sdk';

import { agentstackClient } from '#api/agentstack-client.ts';
import { api } from '#api/index.ts';
import { ensureData, fetchEntity } from '#api/utils.ts';

import type {
  DeleteContextParams,
  ListContextHistoryParams,
  ListContextsParams,
  UpdateContextMetadataParams,
} from './types';

export async function createContext(providerId: string): Promise<CreateContextResponse> {
  return await agentstackClient.createContext(providerId);
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

export async function matchProviders(matchProvidersParams: MatchProvidersParams) {
  return await agentstackClient.matchProviders(matchProvidersParams);
}

export async function createContextToken(createContextTokenParams: CreateContextTokenParams) {
  const result = await agentstackClient.createContextToken(createContextTokenParams);
  return result.token;
}

export async function fetchContextHistory(params: ListContextHistoryParams) {
  return await fetchEntity(() => listContextHistory(params));
}

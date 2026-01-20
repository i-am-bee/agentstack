/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type {
  CreateContextRequest,
  CreateContextTokenRequest,
  DeleteContextRequest,
  ListContextHistoryRequest,
  ListContextsRequest,
} from 'agentstack-sdk';
import { type MatchModelProvidersRequest, unwrapResult } from 'agentstack-sdk';

import { agentStackClient } from '#api/agentstack-client.ts';
import { fetchEntity } from '#api/utils.ts';

import type { PatchContextMetadataRequest } from './types';
import { contextSchema, listContextsResponseSchema } from './types';

export async function listContexts(request: ListContextsRequest) {
  const response = await agentStackClient.listContexts(request);
  const result = unwrapResult(response, listContextsResponseSchema);

  return result;
}

export async function createContext(request: CreateContextRequest) {
  const response = await agentStackClient.createContext(request);
  const result = unwrapResult(response, contextSchema);

  return result;
}

export async function deleteContext(request: DeleteContextRequest) {
  const response = await agentStackClient.deleteContext(request);
  const result = unwrapResult(response);

  return result;
}

export async function listContextHistory(request: ListContextHistoryRequest) {
  const response = await agentStackClient.listContextHistory(request);
  const result = unwrapResult(response);

  return result;
}

export async function patchContextMetadata(request: PatchContextMetadataRequest) {
  const response = await agentStackClient.patchContextMetadata(request);
  const result = unwrapResult(response, contextSchema);

  return result;
}

export async function matchModelProviders(request: MatchModelProvidersRequest) {
  const response = await agentStackClient.matchModelProviders(request);
  const result = unwrapResult(response);

  return result;
}

export async function createContextToken(request: CreateContextTokenRequest) {
  const response = await agentStackClient.createContextToken(request);
  const result = unwrapResult(response);

  return result;
}

export async function fetchContextHistory(request: ListContextHistoryRequest) {
  return await fetchEntity(() => listContextHistory(request));
}

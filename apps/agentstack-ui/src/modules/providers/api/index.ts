/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type {
  CreateProviderRequest,
  DeleteProviderRequest,
  ListProvidersRequest,
  ReadProviderRequest,
} from 'agentstack-sdk';
import { unwrapResult } from 'agentstack-sdk';

import { agentStackClient } from '#api/agentstack-client.ts';
import { fetchEntity } from '#api/utils.ts';

export async function listProviders(request: ListProvidersRequest = {}) {
  const response = await agentStackClient.listProviders(request);
  const result = unwrapResult(response);

  return result;
}

export async function createProvider(request: CreateProviderRequest) {
  const response = await agentStackClient.createProvider(request);
  const result = unwrapResult(response);

  return result;
}

export async function readProvider(request: ReadProviderRequest) {
  const response = await agentStackClient.readProvider(request);
  const result = unwrapResult(response);

  return result;
}

export async function deleteProvider(request: DeleteProviderRequest) {
  const response = await agentStackClient.deleteProvider(request);
  const result = unwrapResult(response);

  return result;
}

export async function fetchProviders(request: ListProvidersRequest = {}) {
  return await fetchEntity(() => listProviders(request));
}

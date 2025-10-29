/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { api } from '#api/index.ts';
import { ensureData } from '#api/utils.ts';

import type { DeleteProviderPath, ListProvidersParams, ReadProviderPath, RegisterProviderRequest } from './types';

export async function listProviders(params: ListProvidersParams = {}) {
  const response = await api.GET('/api/v1/providers', { params });

  return ensureData(response);
}

export async function readProvider(path: ReadProviderPath) {
  const response = await api.GET('/api/v1/providers/{id}', { params: { path } });

  return ensureData(response);
}

export async function deleteProvider(path: DeleteProviderPath) {
  const response = await api.DELETE('/api/v1/providers/{id}', { params: { path } });

  return ensureData(response);
}

export async function registerManagedProvider(body: RegisterProviderRequest) {
  const response = await api.POST('/api/v1/providers', { body });

  return ensureData(response);
}

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { events } from 'fetch-event-stream';

import { api } from '#api/index.ts';
import { ensureData, ensureResponse } from '#api/utils.ts';

import type { DeleteProviderPath, RegisterProviderRequest } from './types';

export async function listProviders() {
  const response = await api.GET('/api/v1/providers');

  return ensureData(response);
}

export async function readProvider(id: string) {
  const response = await api.GET('/api/v1/providers/{id}', { params: { path: { id } } });

  return ensureData(response);
}

export async function deleteProvider({ id }: DeleteProviderPath) {
  const response = await api.DELETE('/api/v1/providers/{id}', { params: { path: { id } } });

  return ensureData(response);
}

export async function registerManagedProvider({ body }: { body: RegisterProviderRequest }) {
  const response = await api.POST('/api/v1/providers', {
    body,
  });
  const stream = events(ensureResponse(response));

  return stream;
}

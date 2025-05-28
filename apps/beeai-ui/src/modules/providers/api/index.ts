/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { events } from 'fetch-event-stream';

import { api } from '#api/index.ts';
import { ensureData, ensureResponse } from '#api/utils.ts';

import type { DeleteProviderPath, RegisterProviderRequest } from './types';

export async function listProviders() {
  const response = await api.GET('/api/v1/providers');

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

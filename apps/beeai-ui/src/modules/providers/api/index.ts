/**
 * Copyright 2025 IBM Corp.
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

import { api } from '#api/index.ts';
import { CreateProviderBody } from './types';

export async function createProvider(body: CreateProviderBody) {
  const response = await api.POST('/api/v1/provider', { body });

  if (response.error) {
    throw new Error('Failed to create provider.');
  }

  return response.data;
}

export async function getProviders() {
  const response = await api.GET('/api/v1/provider');

  if (response.error) {
    throw new Error('Failed to get providers.');
  }

  return response.data;
}

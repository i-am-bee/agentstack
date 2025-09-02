/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { api } from '#api/index.ts';
import { ensureData } from '#api/utils.ts';

import type { UpdateVariablesRequest } from './types';

export async function listVariables(providerId: string) {
  const response = await api.GET('/api/v1/providers/{id}/variables', { params: { path: { id: providerId } } });

  return ensureData(response);
}

export async function updateVariable({
  providerId,
  body,
}: {
  providerId: string;
  body: UpdateVariablesRequest['variables'];
}) {
  const response = await api.PUT('/api/v1/providers/{id}/variables', {
    params: { path: { id: providerId } },
    body: { variables: body },
  });

  return ensureData(response);
}

export async function deleteVariable({ providerId, name }: { providerId: string; name: string }) {
  const response = await api.PUT('/api/v1/providers/{id}/variables', {
    params: { path: { id: providerId } },
    body: { variables: { [name]: null } },
  });

  return ensureData(response);
}

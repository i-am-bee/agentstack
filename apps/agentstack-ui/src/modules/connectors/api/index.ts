/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { api } from '#api/index.ts';
import { ensureData } from '#api/utils.ts';
import { BASE_URL } from '#utils/constants.ts';

import type {
  ConnectConnectorPath,
  CreateConnectorRequest,
  DeleteConnectorPath,
  DisconnectConnectorPath,
} from './types';

export async function createConnector(body: CreateConnectorRequest) {
  const response = await api.POST('/api/v1/connectors', { body });

  return ensureData(response);
}

export async function deleteConnector(path: DeleteConnectorPath) {
  const response = await api.DELETE('/api/v1/connectors/{connector_id}', { params: { path } });

  return ensureData(response);
}

export async function connectConnector(path: ConnectConnectorPath) {
  const response = await api.POST('/api/v1/connectors/{connector_id}/connect', {
    params: { path },
    body: { redirect_url: `${BASE_URL}/oauth-callback` },
  });

  return ensureData(response);
}

export async function disconnectConnector(path: DisconnectConnectorPath) {
  const response = await api.POST('/api/v1/connectors/{connector_id}/disconnect', { params: { path } });

  return ensureData(response);
}

export async function listConnectorPresets() {
  const response = await api.GET('/api/v1/connectors/presets');

  return ensureData(response);
}

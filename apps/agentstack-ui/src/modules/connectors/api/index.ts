/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { api } from '#api/index.ts';
import { ensureData } from '#api/utils.ts';
import { CreateConnectorRequest } from './types';

export async function createConnector(body: CreateConnectorRequest) {
  const response = await api.POST('/api/v1/connectors', { body });
  return ensureData(response);
}

export async function deleteConnector(connectorId: string) {
  const response = await api.DELETE('/api/v1/connectors/{connector_id}', {
    params: { path: { connector_id: connectorId } },
  });
  return ensureData(response);
}

export async function disconnectConnector(connectorId: string) {
  const response = await api.POST('/api/v1/connectors/{connector_id}/disconnect', {
    params: { path: { connector_id: connectorId } },
  });
  return ensureData(response);
}

export async function connectConnector(connectorId: string) {
  const response = await api.POST('/api/v1/connectors/{connector_id}/connect', {
    params: { path: { connector_id: connectorId } },
    body: {
      // TODO: proper URL
      redirect_url: 'http://localhost:3000/oauth-callback',
    },
  });

  return ensureData(response) as AuthRequired;
}

interface AuthRequired {
  id: string;
  url: string;
  state: 'auth_required';
  auth_request: {
    authorization_endpoint: string;
    type: string;
  };
}

interface Connected {
  id: string;
  url: string;
  state: 'connected';
}

interface Disconnected {
  id: string;
  url: string;
  state: 'disconnected';
}

interface Created {
  id: string;
  url: string;
  state: 'created';
}

// TODO: move
type ListConnectorsResponse = {
  items: Array<Created | Connected | Disconnected | AuthRequired>;
};

export async function listConnectors(): Promise<ListConnectorsResponse> {
  const response = await api.GET('/api/v1/connectors', {});
  return ensureData(response) as ListConnectorsResponse;
}

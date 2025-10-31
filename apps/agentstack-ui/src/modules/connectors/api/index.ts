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

export async function connectConnector(connectorId: string) {
  const response = await api.POST('/api/v1/connectors/{connector_id}/connect', {
    params: { path: { connector_id: connectorId } },
    body: {
      // TODO: proper URL
      redirect_url: 'http://localhost:8333/api/v1/connectors/oauth/callback',
    },
  });

  // TODO: proper type
  return ensureData(response);
}

// TODO: move
type ListConnectorsResponse = {
  items: Array<{ id: string; url: string; state: string }>;
};

export async function listConnectors(): Promise<ListConnectorsResponse> {
  const response = await api.GET('/api/v1/connectors', {});
  return ensureData(response) as ListConnectorsResponse;
}

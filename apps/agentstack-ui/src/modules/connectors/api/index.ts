/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ListConnectorsResponse } from 'agentstack-sdk';

import { api } from '#api/index.ts';
import { ensureData } from '#api/utils.ts';
import { BASE_URL } from '#utils/constants.ts';

import type { ConnectConnectorPath, CreateConnectorRequest } from './types';

export async function createConnector(body: CreateConnectorRequest) {
  const response = await api.POST('/api/v1/connectors', { body });

  return ensureData(response);
}

export async function connectConnector(path: ConnectConnectorPath) {
  const response = await api.POST('/api/v1/connectors/{connector_id}/connect', {
    params: { path },
    body: { redirect_url: `${BASE_URL}/oauth-callback` },
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

// eslint-disable-next-line @typescript-eslint/no-unused-vars
interface Connected {
  id: string;
  url: string;
  state: 'connected';
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
interface Disconnected {
  id: string;
  url: string;
  state: 'disconnected';
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
interface Created {
  id: string;
  url: string;
  state: 'created';
}

export async function listConnectors(): Promise<ListConnectorsResponse | undefined> {
  const response = await api.GET('/api/v1/connectors', {});
  return ensureData(response) as ListConnectorsResponse;
}

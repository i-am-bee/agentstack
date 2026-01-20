/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type {
  ConnectConnectorRequest,
  CreateConnectorRequest,
  DeleteConnectorRequest,
  DisconnectConnectorRequest,
} from 'agentstack-sdk';
import { unwrapResult } from 'agentstack-sdk';

import { agentStackClient } from '#api/agentstack-client.ts';
import { BASE_URL } from '#utils/constants.ts';

import { connectorSchema, listConnectorPresetsResponseSchema, listConnectorsResponseSchema } from './types';

export async function listConnectors() {
  const response = await agentStackClient.listConnectors();
  const result = unwrapResult(response, listConnectorsResponseSchema);

  return result;
}

export async function createConnector(request: CreateConnectorRequest) {
  const response = await agentStackClient.createConnector(request);
  const result = unwrapResult(response, connectorSchema);

  return result;
}

export async function deleteConnector(request: DeleteConnectorRequest) {
  const response = await agentStackClient.deleteConnector(request);
  const result = unwrapResult(response);

  return result;
}

export async function connectConnector(request: ConnectConnectorRequest) {
  const response = await agentStackClient.connectConnector({
    redirect_url: `${BASE_URL}/oauth-callback`,
    ...request,
  });
  const result = unwrapResult(response, connectorSchema);

  return result;
}

export async function disconnectConnector(request: DisconnectConnectorRequest) {
  const response = await agentStackClient.disconnectConnector(request);
  const result = unwrapResult(response, connectorSchema);

  return result;
}

export async function listConnectorPresets() {
  const response = await agentStackClient.listConnectorPresets();
  const result = unwrapResult(response, listConnectorPresetsResponseSchema);

  return result;
}

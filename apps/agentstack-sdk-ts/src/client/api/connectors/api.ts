/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { CallApi } from '../core/types';
import { ApiMethod } from '../core/types';
import {
  connectConnectorResponseSchema,
  createConnectorResponseSchema,
  deleteConnectorResponseSchema,
  disconnectConnectorResponseSchema,
  listConnectorPresetsResponseSchema,
  listConnectorsResponseSchema,
  readConnectorResponseSchema,
} from './schemas';
import type {
  ConnectConnectorRequest,
  CreateConnectorRequest,
  DeleteConnectorRequest,
  DisconnectConnectorRequest,
  ReadConnectorRequest,
} from './types';

export function createConnectorsApi(callApi: CallApi) {
  const listConnectors = () =>
    callApi({
      method: ApiMethod.Get,
      path: '/api/v1/connectors',
      schema: listConnectorsResponseSchema,
    });

  const createConnector = ({ ...body }: CreateConnectorRequest) =>
    callApi({
      method: ApiMethod.Post,
      path: '/api/v1/connectors',
      schema: createConnectorResponseSchema,
      body,
    });

  const readConnector = ({ connector_id }: ReadConnectorRequest) =>
    callApi({
      method: ApiMethod.Get,
      path: `/api/v1/connectors/${connector_id}`,
      schema: readConnectorResponseSchema,
    });

  const deleteConnector = ({ connector_id }: DeleteConnectorRequest) =>
    callApi({
      method: ApiMethod.Delete,
      path: `/api/v1/connectors/${connector_id}`,
      schema: deleteConnectorResponseSchema,
    });

  const connectConnector = ({ connector_id, ...body }: ConnectConnectorRequest) =>
    callApi({
      method: ApiMethod.Post,
      path: `/api/v1/connectors/${connector_id}/connect`,
      schema: connectConnectorResponseSchema,
      body,
    });

  const disconnectConnector = ({ connector_id }: DisconnectConnectorRequest) =>
    callApi({
      method: ApiMethod.Post,
      path: `/api/v1/connectors/${connector_id}/disconnect`,
      schema: disconnectConnectorResponseSchema,
    });

  const listConnectorPresets = () =>
    callApi({
      method: ApiMethod.Get,
      path: '/api/v1/connectors/presets',
      schema: listConnectorPresetsResponseSchema,
    });

  return {
    listConnectors,
    createConnector,
    readConnector,
    deleteConnector,
    connectConnector,
    disconnectConnector,
    listConnectorPresets,
  };
}

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ApiPath, ApiRequest, ApiResponse } from '#@types/utils.ts';

export type { Connector, ListConnectorsResponse } from 'agentstack-sdk';

export type CreateConnectorRequest = ApiRequest<'/api/v1/connectors'>;

export type ConnectConnectorPath = ApiPath<'/api/v1/connectors/{connector_id}/connect', 'post'>;

export type DisconnectConnectorPath = ApiPath<'/api/v1/connectors/{connector_id}/disconnect', 'post'>;

export type DeleteConnectorPath = ApiPath<'/api/v1/connectors/{connector_id}', 'delete'>;

export type ListConnectorPresetsResponse = ApiResponse<'/api/v1/connectors/presets'>;

export type ConnectorPreset = Omit<ListConnectorPresetsResponse['items'][number], 'metadata'> & {
  metadata: {
    name?: string;
    description?: string;
  } | null;
};

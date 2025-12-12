/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ApiPath, ApiRequest } from '#@types/utils.ts';

export type CreateConnectorRequest = ApiRequest<'/api/v1/connectors'>;

export type ConnectConnectorPath = ApiPath<'/api/v1/connectors/{connector_id}/connect', 'post'>;

export type DisconnectConnectorPath = ApiPath<'/api/v1/connectors/{connector_id}/disconnect', 'post'>;

export type DeleteConnectorPath = ApiPath<'/api/v1/connectors/{connector_id}', 'delete'>;

export type { Connector, ListConnectorsResponse } from 'agentstack-sdk';

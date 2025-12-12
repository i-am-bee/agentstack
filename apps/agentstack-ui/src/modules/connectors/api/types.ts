/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import {
  connectorSchema as sdkConnectorSchema,
  listConnectorsResponseSchema as sdkListConnectorsResponseSchema,
} from 'agentstack-sdk';
import z from 'zod';

import type { ApiPath, ApiRequest, ApiResponse } from '#@types/utils.ts';

const connectorMetadataSchema = z
  .object({
    name: z.string().optional(),
  })
  .nullable();

export const connectorSchema = sdkConnectorSchema.extend({
  metadata: connectorMetadataSchema,
});

export const listConnectorsResponseSchema = sdkListConnectorsResponseSchema.extend({
  items: z.array(connectorSchema),
});

export type Connector = z.infer<typeof connectorSchema>;

export type ListConnectorsResponse = z.infer<typeof listConnectorsResponseSchema>;

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

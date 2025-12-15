/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type z from 'zod';

import type {
  connectConnectorRequestSchema,
  connectConnectorResponseSchema,
  connectorPresetSchema,
  connectorSchema,
  createConnectorRequestSchema,
  createConnectorResponseSchema,
  deleteConnectorRequestSchema,
  deleteConnectorResponseSchema,
  disconnectConnectorRequestSchema,
  disconnectConnectorResponseSchema,
  listConnectorPresetsRequestSchema,
  listConnectorPresetsResponseSchema,
  listConnectorsRequestSchema,
  listConnectorsResponseSchema,
  readConnectorRequestSchema,
  readConnectorResponseSchema,
} from './schemas';

export enum ConnectorState {
  Created = 'created',
  AuthRequired = 'auth_required',
  Connected = 'connected',
  Disconnected = 'disconnected',
}

export type Connector = z.infer<typeof connectorSchema>;

export type ListConnectorsRequest = z.infer<typeof listConnectorsRequestSchema>;
export type ListConnectorsResponse = z.infer<typeof listConnectorsResponseSchema>;

export type CreateConnectorRequest = z.infer<typeof createConnectorRequestSchema>;
export type CreateConnectorResponse = z.infer<typeof createConnectorResponseSchema>;

export type ReadConnectorRequest = z.infer<typeof readConnectorRequestSchema>;
export type ReadConnectorResponse = z.infer<typeof readConnectorResponseSchema>;

export type DeleteConnectorRequest = z.infer<typeof deleteConnectorRequestSchema>;
export type DeleteConnectorResponse = z.infer<typeof deleteConnectorResponseSchema>;

export type ConnectConnectorRequest = z.infer<typeof connectConnectorRequestSchema>;
export type ConnectConnectorResponse = z.infer<typeof connectConnectorResponseSchema>;

export type DisconnectConnectorRequest = z.infer<typeof disconnectConnectorRequestSchema>;
export type DisconnectConnectorResponse = z.infer<typeof disconnectConnectorResponseSchema>;

export type ConnectorPreset = z.infer<typeof connectorPresetSchema>;

export type ListConnectorPresetsRequest = z.infer<typeof listConnectorPresetsRequestSchema>;
export type ListConnectorPresetsResponse = z.infer<typeof listConnectorPresetsResponseSchema>;

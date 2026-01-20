/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

import { paginatedResponseSchema } from '../core/schemas';
import { ConnectorState } from './types';

export const connectorStateSchema = z.enum(ConnectorState);

export const connectorSchema = z.object({
  id: z.string(),
  url: z.string(),
  state: connectorStateSchema,
  auth_request: z
    .object({
      type: z.literal('code'),
      authorization_endpoint: z.string(),
    })
    .nullable(),
  disconnect_reason: z.string().nullable(),
  metadata: z.record(z.string(), z.string()).nullable(),
});

export const listConnectorsRequestSchema = z.never();

export const listConnectorsResponseSchema = paginatedResponseSchema.extend({
  items: z.array(connectorSchema),
});

export const createConnectorRequestSchema = z.object({
  match_preset: z.boolean(),
  url: z.string(),
  client_id: z.string().nullish(),
  client_secret: z.string().nullish(),
  metadata: z.record(z.string(), z.string()).nullish(),
});

export const createConnectorResponseSchema = connectorSchema;

export const readConnectorRequestSchema = z.object({
  connector_id: z.string(),
});

export const readConnectorResponseSchema = connectorSchema;

export const deleteConnectorRequestSchema = z.object({
  connector_id: z.string(),
});

export const deleteConnectorResponseSchema = z.null();

export const connectConnectorRequestSchema = z.object({
  connector_id: z.string(),
  redirect_url: z.string().nullish(),
});

export const connectConnectorResponseSchema = connectorSchema;

export const disconnectConnectorRequestSchema = z.object({
  connector_id: z.string(),
});

export const disconnectConnectorResponseSchema = connectorSchema;

export const connectorPresetSchema = z.object({
  url: z.string(),
  metadata: z.record(z.string(), z.string()).nullable(),
});

export const listConnectorPresetsRequestSchema = z.never();

export const listConnectorPresetsResponseSchema = paginatedResponseSchema.extend({
  items: z.array(connectorPresetSchema),
});

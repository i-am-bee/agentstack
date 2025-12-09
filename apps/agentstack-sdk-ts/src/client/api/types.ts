/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

export const contextSchema = z.object({
  id: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
  last_active_at: z.string(),
  created_by: z.string(),
  provider_id: z.string().nullable(),
  metadata: z.record(z.string(), z.unknown()).nullable(),
});
export type CreateContextResponse = z.infer<typeof contextSchema>;

export const contextTokenSchema = z.object({
  token: z.string(),
  expires_at: z.string().nullable(),
});
export type ContextToken = z.infer<typeof contextTokenSchema>;

export enum ModelCapability {
  Llm = 'llm',
  Embedding = 'embedding',
}

const paginatedResultSchema = z.object({
  items: z.array(z.unknown()),
  total_count: z.number(),
  has_more: z.boolean(),
  next_page_token: z.string().nullable(),
});

export const modelProviderMatchSchema = paginatedResultSchema.extend({
  items: z.array(
    z.object({
      model_id: z.string(),
      score: z.number(),
    }),
  ),
});
export type ModelProviderMatch = z.infer<typeof modelProviderMatchSchema>;

export const resourceIdPermissionSchema = z.object({
  id: z.string(),
});

export type ResourceIdPermission = z.infer<typeof resourceIdPermissionSchema>;

export const contextPermissionsGrantSchema = z.object({
  files: z.array(z.literal(['read', 'write', 'extract', '*'])).optional(),
  vector_stores: z.array(z.literal(['read', 'write', '*'])).optional(),
  context_data: z.array(z.literal(['read', 'write', '*'])).optional(),
});

export type ContextPermissionsGrant = z.infer<typeof contextPermissionsGrantSchema>;

export const globalPermissionsGrantSchema = contextPermissionsGrantSchema.extend({
  feedback: z.array(z.literal('write')).optional(),

  llm: z.array(z.union([z.literal('*'), resourceIdPermissionSchema])).optional(),
  embeddings: z.array(z.union([z.literal('*'), resourceIdPermissionSchema])).optional(),
  model_providers: z.array(z.literal(['read', 'write', '*'])).optional(),

  a2a_proxy: z.array(z.literal('*')).optional(),

  providers: z.array(z.literal(['read', 'write', '*'])).optional(),
  provider_variables: z.array(z.literal(['read', 'write', '*'])).optional(),

  contexts: z.array(z.literal(['read', 'write', '*'])).optional(),

  mcp_providers: z.array(z.literal(['read', 'write', '*'])).optional(),
  mcp_tools: z.array(z.literal(['read', '*'])).optional(),
  mcp_proxy: z.array(z.literal('*')).optional(),

  connectors: z.array(z.literal(['read', 'write', 'proxy', '*'])).optional(),
});

export type GlobalPermissionsGrant = z.infer<typeof globalPermissionsGrantSchema>;

export enum ConnectorState {
  Created = 'created',
  AuthRequired = 'auth_required',
  Connected = 'connected',
  Disconnected = 'disconnected',
}

export const connectorSchema = z.object({
  id: z.string(),
  url: z.string(),
  state: z.enum(ConnectorState),
  auth_request: z
    .object({
      type: z.literal('code'),
      authorization_endpoint: z.string(),
    })
    .nullable(),
  disconnect_reason: z.string().nullable(),
  metadata: z.record(z.string(), z.string()).nullable(),
});

export type Connector = z.infer<typeof connectorSchema>;

export const listConnectorsResponseSchema = paginatedResultSchema.extend({
  items: z.array(connectorSchema),
});

export type ListConnectorsResponse = z.infer<typeof listConnectorsResponseSchema>;

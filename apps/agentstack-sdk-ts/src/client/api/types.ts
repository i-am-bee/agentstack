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

interface ResourceIdPermission {
  id: string;
}

export interface ContextPermissionsGrant {
  files?: ('read' | 'write' | 'extract' | '*')[];
  vector_stores?: ('read' | 'write' | '*')[];
  context_data?: ('read' | 'write' | '*')[];
}

export interface GlobalPermissionsGrant extends ContextPermissionsGrant {
  llm?: ('*' | ResourceIdPermission)[];
  embeddings?: ('*' | ResourceIdPermission)[];
  a2a_proxy?: '*'[];
  model_providers?: ('read' | 'write' | '*')[];
  variables?: ('read' | 'write' | '*')[];

  providers?: ('read' | 'write' | '*')[];
  provider_variables?: ('read' | 'write' | '*')[];

  contexts?: ('read' | 'write' | '*')[];
  mcp_providers?: ('read' | 'write' | '*')[];
  mcp_tools?: ('read' | '*')[];
  mcp_proxy?: '*'[];

  connectors?: ('read' | 'write' | 'proxy' | '*')[];
}

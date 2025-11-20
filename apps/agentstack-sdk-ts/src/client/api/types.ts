/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { z } from 'zod';

export const contextSchema = z.object({
  id: z.string(),
  created_at: z.string().optional(),
  created_by: z.string(),
  last_active_at: z.string(),
  provider_id: z.string().nullable(),
  updated_at: z.string(),
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

export interface GlobalPermissionGrant {
  a2a_proxy?: '*'[];
  connectors?: ('read' | 'write' | 'proxy' | '*')[];
  context_data?: ('read' | 'write' | '*')[];
  contexts?: ('read' | 'write' | '*')[];
  embeddings?: ('*' | ResourceIdPermission)[];
  feedback?: 'write'[];
  files?: ('read' | 'write' | 'extract' | '*')[];
  llm?: ('*' | ResourceIdPermission)[];
  mcp_providers?: ('read' | 'write' | '*')[];
  mcp_proxy?: '*'[];
  mcp_tools?: ('read' | '*')[];
  model_providers?: ('read' | 'write' | '*')[];
  provider_variables?: ('read' | 'write' | '*')[];
  providers?: ('read' | 'write' | '*')[];
  vector_stores?: ('read' | 'write' | 'extract' | '*')[];
}

export interface ContextPermissionGrant {
  context_data?: ('read' | 'write' | '*')[];
  files?: ('read' | 'write' | 'extract' | '*')[];
  vector_stores?: ('read' | 'write' | 'extract' | '*')[];
}

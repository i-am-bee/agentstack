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
  expires_at: z.string(),
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

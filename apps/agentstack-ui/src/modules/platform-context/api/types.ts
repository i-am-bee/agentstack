/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ContextHistory } from 'agentstack-sdk';
import {
  contextSchema as sdkContextSchema,
  listContextsResponseSchema as sdkListContextsResponseSchema,
  patchContextMetadataRequestSchema as sdkPatchContextMetadataRequestSchema,
} from 'agentstack-sdk';
import z from 'zod';

export enum TitleGenerationState {
  Pending = 'pending',
  Completed = 'completed',
  Failed = 'failed',
}

export const contextMetadataSchema = z.object({
  agent_name: z.string().optional(),
  provider_id: z.string().optional(),
  title_generation_state: z.enum(TitleGenerationState).optional(),
  title: z.string().optional(),
});

export type ContextMetadata = z.infer<typeof contextMetadataSchema>;

export const contextSchema = sdkContextSchema.extend({
  metadata: contextMetadataSchema.nullable(),
});
export type Context = z.infer<typeof contextSchema>;

export const listContextsResponseSchema = sdkListContextsResponseSchema.extend({
  items: z.array(contextSchema),
});
export type ListContextsResponse = z.infer<typeof listContextsResponseSchema>;

export const patchContextMetadataRequestSchema = sdkPatchContextMetadataRequestSchema.extend({
  metadata: contextMetadataSchema,
});
export type PatchContextMetadataRequest = z.infer<typeof patchContextMetadataRequestSchema>;

//

export type HistoryItem = ContextHistory['data'];
export type HistoryMessage = Extract<HistoryItem, { kind: 'message' }>;

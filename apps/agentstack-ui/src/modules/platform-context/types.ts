/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { contextPermissionsGrantSchema, globalPermissionsGrantSchema } from 'agentstack-sdk';
import z from 'zod';

import type { ListContextsResponse } from './api/types';

enum TitleGenerationState {
  Pending = 'pending',
  Completed = 'completed',
  Failed = 'failed',
}

export enum ModelCapability {
  Llm = 'llm',
  Embedding = 'embedding',
}

export type ContextMetadata = {
  agent_name?: string;
  provider_id?: string;
  title_generation_state?: TitleGenerationState;
  title?: string;
};

export type ContextWithMetadata = ListContextsResponse['items'][number] & { metadata?: ContextMetadata };

export const contextTokenPermissionsSchema = z.object({
  grant_global_permissions: globalPermissionsGrantSchema.optional(),
  grant_context_permissions: contextPermissionsGrantSchema.optional(),
});

export type ContextTokenPermissions = z.infer<typeof contextTokenPermissionsSchema>;

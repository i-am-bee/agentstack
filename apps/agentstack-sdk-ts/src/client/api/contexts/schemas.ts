/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

import { artifactSchema, messageSchema } from '../../a2a/protocol/schemas';
import { paginatedResponseSchema, paginationQuerySchema } from '../core/schemas';
import { ContextHistoryKind } from './types';

export const contextSchema = z.object({
  id: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
  last_active_at: z.string(),
  created_by: z.string(),
  provider_id: z.string().nullable(),
  metadata: z.record(z.string(), z.unknown()).nullable(),
});

export const listContextsRequestSchema = z.object({
  query: paginationQuerySchema
    .extend({
      provider_id: z.string().nullish(),
      include_empty: z.boolean().optional(),
    })
    .optional(),
});

export const listContextsResponseSchema = paginatedResponseSchema.extend({
  items: z.array(contextSchema),
});

export const createContextRequestSchema = z.object({
  provider_id: z.string().nullish(),
  metadata: z.record(z.string(), z.string()).nullish(),
});

export const createContextResponseSchema = contextSchema;

export const readContextRequestSchema = z.object({
  context_id: z.string(),
});

export const readContextResponseSchema = contextSchema;

export const updateContextRequestSchema = z.object({
  context_id: z.string(),
  metadata: z.record(z.string(), z.string()).nullish(),
});

export const updateContextResponseSchema = contextSchema;

export const deleteContextRequestSchema = z.object({
  context_id: z.string(),
});

export const deleteContextResponseSchema = z.null();

export const contextHistoryKind = z.enum(ContextHistoryKind);

export const contextHistorySchema = z.object({
  id: z.string(),
  context_id: z.string(),
  created_at: z.string(),
  kind: contextHistoryKind,
  data: z.union([artifactSchema, messageSchema]),
});

export const listContextHistoryRequestSchema = z.object({
  context_id: z.string(),
  query: paginationQuerySchema.optional(),
});

export const listContextHistoryResponseSchema = paginatedResponseSchema.extend({
  items: z.array(contextHistorySchema),
});

export const createContextHistoryRequestSchema = z.object({
  context_id: z.string(),
  data: z.union([artifactSchema, messageSchema]),
});

export const createContextHistoryResponseSchema = z.null();

export const patchContextMetadataRequestSchema = z.object({
  context_id: z.string(),
  metadata: z.record(z.string(), z.union([z.string(), z.null()])),
});

export const patchContextMetadataResponseSchema = contextSchema;

export const contextTokenSchema = z.object({
  token: z.string(),
  expires_at: z.string().nullable(),
});

export const resourceIdPermissionSchema = z.object({
  id: z.string(),
});

export const contextPermissionsGrantSchema = z.object({
  files: z.array(z.literal(['read', 'write', 'extract', '*'])).optional(),
  vector_stores: z.array(z.literal(['read', 'write', '*'])).optional(),
  context_data: z.array(z.literal(['read', 'write', '*'])).optional(),
});

export const globalPermissionsGrantSchema = contextPermissionsGrantSchema
  .extend({
    feedback: z.array(z.literal('write')).optional(),

    llm: z.array(z.union([z.literal('*'), resourceIdPermissionSchema])).optional(),
    embeddings: z.array(z.union([z.literal('*'), resourceIdPermissionSchema])).optional(),
    model_providers: z.array(z.literal(['read', 'write', '*'])).optional(),

    a2a_proxy: z.array(z.union([z.literal('*'), z.string()])).optional(),

    providers: z.array(z.literal(['read', 'write', '*'])).optional(),
    provider_variables: z.array(z.literal(['read', 'write', '*'])).optional(),

    contexts: z.array(z.literal(['read', 'write', '*'])).optional(),

    connectors: z.array(z.literal(['read', 'write', 'proxy', '*'])).optional(),
  })
  .superRefine((val, ctx) => {
    if (!val.a2a_proxy) return;

    if (val.a2a_proxy.length === 0) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'a2a_proxy cannot be empty array',
        path: ['a2a_proxy'],
      });
      return;
    }

    const hasWildcard = val.a2a_proxy.includes('*');
    const hasOthers = val.a2a_proxy.some((v) => v !== '*');

    if (hasWildcard && hasOthers) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "a2a_proxy cannot mix '*' with specific providers",
        path: ['a2a_proxy'],
      });
    }
  });

export const createContextTokenRequestSchema = z.object({
  context_id: z.string(),
  grant_context_permissions: contextPermissionsGrantSchema.optional(),
  grant_global_permissions: globalPermissionsGrantSchema.optional(),
});

export const createContextTokenResponseSchema = contextTokenSchema;

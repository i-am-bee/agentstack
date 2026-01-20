/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type z from 'zod';

import type {
  contextHistorySchema,
  contextPermissionsGrantSchema,
  contextSchema,
  contextTokenSchema,
  createContextHistoryRequestSchema,
  createContextHistoryResponseSchema,
  createContextRequestSchema,
  createContextResponseSchema,
  createContextTokenRequestSchema,
  createContextTokenResponseSchema,
  deleteContextRequestSchema,
  deleteContextResponseSchema,
  globalPermissionsGrantSchema,
  listContextHistoryRequestSchema,
  listContextHistoryResponseSchema,
  listContextsRequestSchema,
  listContextsResponseSchema,
  patchContextMetadataRequestSchema,
  patchContextMetadataResponseSchema,
  readContextRequestSchema,
  readContextResponseSchema,
  resourceIdPermissionSchema,
  updateContextRequestSchema,
  updateContextResponseSchema,
} from './schemas';

export type Context = z.infer<typeof contextSchema>;

export type ListContextsRequest = z.infer<typeof listContextsRequestSchema>;
export type ListContextsResponse = z.infer<typeof listContextsResponseSchema>;

export type CreateContextRequest = z.infer<typeof createContextRequestSchema>;
export type CreateContextResponse = z.infer<typeof createContextResponseSchema>;

export type ReadContextRequest = z.infer<typeof readContextRequestSchema>;
export type ReadContextResponse = z.infer<typeof readContextResponseSchema>;

export type UpdateContextRequest = z.infer<typeof updateContextRequestSchema>;
export type UpdateContextResponse = z.infer<typeof updateContextResponseSchema>;

export type DeleteContextRequest = z.infer<typeof deleteContextRequestSchema>;
export type DeleteContextResponse = z.infer<typeof deleteContextResponseSchema>;

export enum ContextHistoryKind {
  Artifact = 'artifact',
  Message = 'message',
}
export type ContextHistory = z.infer<typeof contextHistorySchema>;

export type ListContextHistoryRequest = z.infer<typeof listContextHistoryRequestSchema>;
export type ListContextHistoryResponse = z.infer<typeof listContextHistoryResponseSchema>;

export type CreateContextHistoryRequest = z.infer<typeof createContextHistoryRequestSchema>;
export type CreateContextHistoryResponse = z.infer<typeof createContextHistoryResponseSchema>;

export type PatchContextMetadataRequest = z.infer<typeof patchContextMetadataRequestSchema>;
export type PatchContextMetadataResponse = z.infer<typeof patchContextMetadataResponseSchema>;

export type ContextToken = z.infer<typeof contextTokenSchema>;

export type ResourceIdPermission = z.infer<typeof resourceIdPermissionSchema>;
export type ContextPermissionsGrant = z.infer<typeof contextPermissionsGrantSchema>;
export type GlobalPermissionsGrant = z.infer<typeof globalPermissionsGrantSchema>;

export type CreateContextTokenRequest = z.infer<typeof createContextTokenRequestSchema>;
export type CreateContextTokenResponse = z.infer<typeof createContextTokenResponseSchema>;

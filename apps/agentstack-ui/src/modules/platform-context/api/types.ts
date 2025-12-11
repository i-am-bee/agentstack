/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ApiPath, ApiQuery, ApiRequest, ApiResponse } from '#@types/utils.ts';

import type { ContextMetadata } from '../types';

export type { CreateContextResponse } from 'agentstack-sdk';

export type ListContextsQuery = ApiQuery<'/api/v1/contexts'>;
export type ListContextsResponse = ApiResponse<'/api/v1/contexts'>;
export type ListContextsParams = { query?: ListContextsQuery };

export type DeleteContextPath = ApiPath<'/api/v1/contexts/{context_id}'>;
export type DeleteContextParams = DeleteContextPath;

export type UpdateContextMetadataPath = ApiPath<'/api/v1/contexts/{context_id}/metadata', 'patch'>;
export type UpdateContextMetadataRequest = ApiRequest<'/api/v1/contexts/{context_id}/metadata', 'patch'> & {
  metadata: Pick<ContextMetadata, 'agent_name' | 'provider_id'>;
};
export type UpdateContextMetadataParams = UpdateContextMetadataPath & UpdateContextMetadataRequest;

export type ListContextHistoryQuery = ApiQuery<'/api/v1/contexts/{context_id}/history'>;
export type ListContextHistoryResponse = ApiResponse<'/api/v1/contexts/{context_id}/history'>;
export type ListContextHistoryParams = { contextId: string; query?: ListContextHistoryQuery };

export type ContextHistoryItem = ListContextHistoryResponse['items'][number];

export type HistoryItem = ApiResponse<'/api/v1/contexts/{context_id}/history'>['items'][number]['data'];
export type HistoryMessage = Extract<HistoryItem, { kind: 'message' }>;
export type HistoryArtifact = Extract<HistoryItem, { artifactId: string }>;

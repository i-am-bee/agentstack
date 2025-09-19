/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ApiPath, ApiQuery, ApiRequest, ApiResponse } from '#@types/utils.ts';

import type { ContextMetadata, ModelCapability } from '../types';

type CreateContextRequest = ApiRequest<'/api/v1/contexts'>;
export type CreateContextParams = CreateContextRequest & {
  metadata: Required<Pick<ContextMetadata, 'agent_name' | 'provider_id'>>;
};

export type ListContextsQuery = ApiQuery<'/api/v1/contexts'>;
export type ListContextsResponse = ApiResponse<'/api/v1/contexts'>;
export type ListContextsParams = { query?: ListContextsQuery };

type DeleteContextPath = ApiPath<'/api/v1/contexts/{context_id}'>;
export type DeleteContextParams = DeleteContextPath;

export type ListContextHistoryQuery = ApiQuery<'/api/v1/contexts/{context_id}/history'>;
export type ListContextHistoryResponse = ApiResponse<'/api/v1/contexts/{context_id}/history'>;
export type ListContextHistoryParams = { contextId: string; query?: ListContextHistoryQuery };

export type ContextHistoryItem = ListContextHistoryResponse['items'][number];

export type CreateContextTokenPath = ApiPath<'/api/v1/contexts/{context_id}/token', 'post'>;
export type CreateContextTokenRequest = ApiRequest<'/api/v1/contexts/{context_id}/token'>;
export type CreateContextTokenParams = CreateContextTokenPath & CreateContextTokenRequest;

export type MatchModelProvidersRequest = ApiRequest<'/api/v1/model_providers/match'>;
export type MatchModelProvidersParams = Omit<MatchModelProvidersRequest, 'score_cutoff' | 'capability'> & {
  capability: ModelCapability;
};

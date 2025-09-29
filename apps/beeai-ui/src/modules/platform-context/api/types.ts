/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ApiPath, ApiRequest } from '#@types/utils.ts';

import type { ModelCapability } from '../types';

export type CreateContextRequest = ApiRequest<'/api/v1/contexts'>;

export type CreateContextTokenPath = ApiPath<'/api/v1/contexts/{context_id}/token', 'post'>;
export type CreateContextTokenRequest = ApiRequest<'/api/v1/contexts/{context_id}/token'>;
export type CreateContextTokenParams = CreateContextTokenPath & CreateContextTokenRequest;

export type MatchModelProvidersRequest = ApiRequest<'/api/v1/model_providers/match'>;
export type MatchModelProvidersParams = Omit<MatchModelProvidersRequest, 'score_cutoff' | 'capability'> & {
  capability: ModelCapability;
};

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ApiPath, ApiRequest, ApiResponse, RemoveIndexSignature } from '#@types/utils.ts';
import type { StreamErrorResponse } from '#api/types.ts';

export type ProvidersListResponse = ApiResponse<'/api/v1/providers'>;

export type Provider = RemoveIndexSignature<ProvidersListResponse['items'][number]>;

export type ProviderLocation = Provider['source'];

export type ReadProviderPath = ApiPath<'/api/v1/providers/{id}'>;

export type DeleteProviderPath = ApiPath<'/api/v1/providers/{id}', 'delete'>;

export type RegisterProviderRequest = ApiRequest<'/api/v1/providers'>;

export enum ProviderStatus {
  Missing = 'missing',
  Starting = 'starting',
  Ready = 'ready',
  Running = 'running',
  Error = 'error',
}

export type MissingEnvs = Provider['missing_configuration'];

export interface ProviderImportMessageEvent {
  stream: 'stdout' | 'stderr';
  message: string;
  time: string;
}

export interface ProviderImportErrorEvent {
  error: StreamErrorResponse;
}

export type ProviderImportEvent = ProviderImportMessageEvent | ProviderImportErrorEvent;

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import type { ApiPath, ApiRequest, ApiResponse } from '#@types/utils.ts';

export type ProvidersList = ApiResponse<'/api/v1/providers'>;

export type Provider = ProvidersList['items'][number];

export type DeleteProviderPath = ApiPath<'/api/v1/providers/{id}', 'delete'>;

export type InstallProviderPath = ApiPath<'/api/v1/providers/{id}/install', 'put'>;

export type RegisterManagedProviderRequest = ApiRequest<'/api/v1/providers/register/managed'>;

export type RegisterManagedProviderResponse = ApiResponse<'/api/v1/providers/register/managed', 'post'>;

export enum ProviderStatus {
  NotLoaded = 'not_loaded',
  NotInstalled = 'not_installed',
  InstallError = 'install_error',
  Installing = 'installing',
  Starting = 'starting',
  Ready = 'ready',
  Running = 'running',
  Error = 'error',
}

export type MissingEnvs = Provider['missing_configuration'];

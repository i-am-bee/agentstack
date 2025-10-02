/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ApiPath, ApiRequest } from '#@types/utils.ts';

export type ListVariablesPath = ApiPath<'/api/v1/providers/{id}/variables'>;

export type UpdateVariablePath = ApiPath<'/api/v1/providers/{id}/variables', 'put'>;
export type UpdateVariablesRequest = ApiRequest<'/api/v1/providers/{id}/variables', 'put'>;
export type UpdateVariableParams = UpdateVariablePath & UpdateVariablesRequest;

export type DeleteVariableRequest = { name: string };
export type DeleteVariableParams = UpdateVariablePath & DeleteVariableRequest;

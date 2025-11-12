/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ApiRequest, ApiResponse } from '#@types/utils.ts';

export type CreateConnectorRequest = ApiRequest<'/api/v1/connectors'>;
export type ListConnectorsResponse = ApiResponse<'/api/v1/connectors', 'get', 'application/json', 200>;

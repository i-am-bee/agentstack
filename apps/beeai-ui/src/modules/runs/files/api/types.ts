/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ApiPath, ApiRequest, ApiResponse } from '#@types/utils.ts';

export type UploadFileRequest = ApiRequest<'/api/v1/files', 'post', 'multipart/form-data'>;

export type UploadFileResponse = ApiResponse<'/api/v1/files', 'post', 'application/json', 201>;

export type DeleteFilePath = ApiPath<'/api/v1/files/{file_id}', 'delete'>;

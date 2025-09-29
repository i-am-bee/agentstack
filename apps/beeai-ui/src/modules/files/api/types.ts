/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ApiPath, ApiQuery, ApiRequest, ApiResponse } from '#@types/utils.ts';

import type { FileEntity } from '../types';

export type UploadFileQuery = ApiQuery<'/api/v1/files', 'post'>;
export type UploadFileRequest = ApiRequest<'/api/v1/files', 'post', 'multipart/form-data'>;
export type UploadFileParams = UploadFileQuery & Omit<UploadFileRequest, 'file'> & { file: FileEntity };
export type UploadFileResponse = ApiResponse<'/api/v1/files', 'post', 'application/json', 201>;

export type DeleteFileQuery = ApiQuery<'/api/v1/files/{file_id}', 'delete'>;
export type DeleteFilePath = ApiPath<'/api/v1/files/{file_id}', 'delete'>;
export type DeleteFileParams = DeleteFilePath & DeleteFileQuery;

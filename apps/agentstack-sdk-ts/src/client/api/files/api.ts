/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { CallApi } from '../core/types';
import { ApiMethod } from '../core/types';
import {
  createFileResponseSchema,
  deleteFileResponseSchema,
  readFileContentResponseSchema,
  readFileResponseSchema,
} from './schemas';
import type { CreateFileRequest, DeleteFileRequest, ReadFileContentRequest, ReadFileRequest } from './types';

export function createFilesApi(callApi: CallApi) {
  const createFile = ({ context_id, file }: CreateFileRequest) => {
    const body = new FormData();

    if (file instanceof File) {
      body.append('file', file);
    } else {
      body.append('file', file.blob, file.filename);
    }

    return callApi({
      method: ApiMethod.Post,
      path: '/api/v1/files',
      schema: createFileResponseSchema,
      query: { context_id },
      body,
    });
  };

  const readFile = ({ context_id, file_id }: ReadFileRequest) =>
    callApi({
      method: ApiMethod.Get,
      path: `/api/v1/files/${file_id}`,
      schema: readFileResponseSchema,
      query: { context_id },
    });

  const deleteFile = ({ context_id, file_id }: DeleteFileRequest) =>
    callApi({
      method: ApiMethod.Delete,
      path: `/api/v1/files/${file_id}`,
      schema: deleteFileResponseSchema,
      query: { context_id },
    });

  const readFileContent = ({ context_id, file_id }: ReadFileContentRequest) =>
    callApi({
      method: ApiMethod.Get,
      path: `/api/v1/files/${file_id}/content`,
      schema: readFileContentResponseSchema,
      query: { context_id },
    });

  return {
    createFile,
    readFile,
    deleteFile,
    readFileContent,
  };
}

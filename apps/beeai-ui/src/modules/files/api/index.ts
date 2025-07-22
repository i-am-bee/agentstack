/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { api } from '#api/index.ts';
import { ensureData } from '#api/utils.ts';

import type { FileEntity } from '../types';
import type { DeleteFilePath, UploadFileRequest } from './types';

export async function uploadFile({ body }: { body: Omit<UploadFileRequest, 'file'> & { file: FileEntity } }) {
  const response = await api.POST('/api/v1/files', {
    body: { ...body, file: body.file.originalFile } as unknown as UploadFileRequest,
    bodySerializer: (body) => {
      const formData = new FormData();

      formData.append('file', body.file);

      return formData;
    },
  });

  return ensureData(response);
}

export async function deleteFile({ file_id }: DeleteFilePath) {
  const response = await api.DELETE('/api/v1/files/{file_id}', { params: { path: { file_id } } });

  return ensureData(response);
}

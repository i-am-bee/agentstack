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

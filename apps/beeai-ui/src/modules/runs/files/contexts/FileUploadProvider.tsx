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

import { type PropsWithChildren, useCallback, useMemo, useState } from 'react';
import { type FileRejection, useDropzone } from 'react-dropzone';
import { v4 as uuid } from 'uuid';

import { useToast } from '#contexts/Toast/index.ts';

import { MAX_FILES } from '../constants';
import type { FileEntity } from '../types';
import { FileUploadContext } from './file-upload-context';

export function FileUploadProvider({ children }: PropsWithChildren) {
  const [files, setFiles] = useState<FileEntity[]>([]);

  const { addToast } = useToast();

  const onDropAccepted = useCallback((acceptedFiles: File[]) => {
    const newFiles = acceptedFiles.map((file) =>
      Object.assign(file, {
        id: uuid(),
      }),
    );

    setFiles((files) => [...files, ...newFiles]);
  }, []);

  const onDropRejected = useCallback(
    (fileRejections: FileRejection[]) => {
      fileRejections.forEach(({ errors, file }) => {
        addToast({
          title: `File ${file.name} was rejected`,
          subtitle: errors.map(({ message }) => message).join('\n'),
          timeout: 5_000,
        });
      });
    },
    [addToast],
  );

  const clearFiles = useCallback(() => {
    setFiles([]);
  }, []);

  const removeFile = useCallback((id: string) => {
    setFiles((files) => files.filter((file) => file.id !== id));
  }, []);

  const dropzone = useDropzone({
    // TODO:
    // accept: {
    //   'image/*': [],
    // },
    noClick: true,
    noKeyboard: true,
    maxFiles: MAX_FILES,
    onDropAccepted,
    onDropRejected,
  });

  const contextValue = useMemo(
    () => ({
      files,
      dropzone,
      removeFile,
      clearFiles,
    }),
    [files, dropzone, removeFile, clearFiles],
  );

  return <FileUploadContext.Provider value={contextValue}>{children}</FileUploadContext.Provider>;
}

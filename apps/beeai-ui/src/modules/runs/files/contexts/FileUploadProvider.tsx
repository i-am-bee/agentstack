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

import { useDeleteFile } from '../api/mutations/useDeleteFile';
import { useUploadFile } from '../api/mutations/useUploadFile';
import { ALLOWED_FILES, MAX_FILE_SIZE, MAX_FILES } from '../constants';
import { type FileEntity, FileStatus } from '../types';
import { FileUploadContext } from './file-upload-context';

export function FileUploadProvider({ children }: PropsWithChildren) {
  const [files, setFiles] = useState<FileEntity[]>([]);

  const { addToast } = useToast();
  const { mutateAsync: uploadFile } = useUploadFile({
    onMutate: ({ file: { id } }) => {
      setFiles((files) => files.map((file) => (file.id === id ? { ...file, status: FileStatus.Uploading } : file)));
    },
    onSuccess: (data, { file: { id } }) => {
      setFiles((files) =>
        files.map((file) => (file.id === id ? { ...file, status: FileStatus.Completed, uploadFile: data } : file)),
      );
    },
    onError: (error, { file: { id } }) => {
      setFiles((files) =>
        files.map((file) => (file.id === id ? { ...file, status: FileStatus.Failed, error: error.message } : file)),
      );
    },
  });
  const { mutateAsync: deleteFile } = useDeleteFile();

  const onDropAccepted = useCallback(
    async (acceptedFiles: File[]) => {
      const newFiles = acceptedFiles.map((file) => ({ id: uuid(), originalFile: file, status: FileStatus.Idle }));

      setFiles((files) => [...files, ...newFiles]);

      newFiles.forEach((file) => {
        uploadFile({ file });
      });
    },
    [uploadFile],
  );

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

  const removeFile = useCallback(
    (id: string) => {
      const uploadFileId = files.find((file) => file.id === id)?.uploadFile?.id;

      if (uploadFileId) {
        deleteFile({ file_id: uploadFileId });
      }

      setFiles((files) => files.filter((file) => file.id !== id));
    },
    [files, deleteFile],
  );

  const isPending = useMemo(
    () => files.some(({ status }) => status !== FileStatus.Completed && status !== FileStatus.Failed),
    [files],
  );

  const dropzone = useDropzone({
    accept: ALLOWED_FILES,
    noClick: true,
    noKeyboard: true,
    maxFiles: MAX_FILES,
    maxSize: MAX_FILE_SIZE,
    onDropAccepted,
    onDropRejected,
  });

  const contextValue = useMemo(
    () => ({
      files,
      isPending,
      dropzone,
      removeFile,
      clearFiles,
    }),
    [files, isPending, dropzone, removeFile, clearFiles],
  );

  return <FileUploadContext.Provider value={contextValue}>{children}</FileUploadContext.Provider>;
}

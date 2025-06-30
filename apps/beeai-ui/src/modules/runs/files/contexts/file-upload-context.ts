/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { createContext } from 'react';
import type { DropzoneState } from 'react-dropzone';

import { noop } from '#utils/helpers.ts';

import type { FileEntity } from '../types';

export const FileUploadContext = createContext<FileUploadContextValue>({
  files: [],
  isPending: false,
  removeFile: noop,
  clearFiles: noop,
});

interface FileUploadContextValue {
  files: FileEntity[];
  isPending: boolean;
  dropzone?: DropzoneState;
  removeFile: (id: string) => void;
  clearFiles: () => void;
}

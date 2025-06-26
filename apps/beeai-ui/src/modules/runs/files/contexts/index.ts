/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { use } from 'react';

import { FileUploadContext } from './file-upload-context';

export function useFileUpload() {
  const context = use(FileUploadContext);

  if (!context) {
    throw new Error('useFileUpload must be used within a FileUploadProvider');
  }

  return context;
}

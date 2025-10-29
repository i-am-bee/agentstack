/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { UploadFileResponse } from './api/types';

export interface FileEntity {
  id: string;
  originalFile: File;
  status: FileStatus;
  uploadFile?: UploadFileResponse;
  error?: string;
}

export enum FileStatus {
  Idle = 'idle',
  Uploading = 'uploading',
  Completed = 'completed',
  Failed = 'failed',
}

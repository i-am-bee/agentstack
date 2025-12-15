/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type z from 'zod';

import type {
  createFileRequestSchema,
  createFileResponseSchema,
  deleteFileRequestSchema,
  deleteFileResponseSchema,
  fileSchema,
  readFileContentRequestSchema,
  readFileContentResponseSchema,
  readFileRequestSchema,
  readFileResponseSchema,
} from './schemas';

export enum FileType {
  UserUpload = 'user_upload',
  ExtractedText = 'extracted_text',
}

export type File = z.infer<typeof fileSchema>;

export type CreateFileRequest = z.infer<typeof createFileRequestSchema>;
export type CreateFileResponse = z.infer<typeof createFileResponseSchema>;

export type ReadFileRequest = z.infer<typeof readFileRequestSchema>;
export type ReadFileResponse = z.infer<typeof readFileResponseSchema>;

export type DeleteFileRequest = z.infer<typeof deleteFileRequestSchema>;
export type DeleteFileResponse = z.infer<typeof deleteFileResponseSchema>;

export type ReadFileContentRequest = z.infer<typeof readFileContentRequestSchema>;
export type ReadFileContentResponse = z.infer<typeof readFileContentResponseSchema>;

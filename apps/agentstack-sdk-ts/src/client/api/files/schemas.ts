/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

import { FileType } from './types';

export const fileTypeSchema = z.enum(FileType);

export const fileSchema = z.object({
  id: z.string(),
  filename: z.string(),
  content_type: z.string(),
  file_type: fileTypeSchema,
  created_by: z.string(),
  created_at: z.string(),
  context_id: z.string().nullish(),
  file_size_bytes: z.number().nullish(),
  parent_file_id: z.string().nullish(),
});

export const createFileRequestSchema = z.object({
  context_id: z.string().nullable(),
  file: z.union([
    z.file(),
    z.object({
      blob: z.instanceof(Blob),
      filename: z.string(),
    }),
  ]),
});

export const createFileResponseSchema = fileSchema;

export const readFileRequestSchema = z.object({
  context_id: z.string().nullable(),
  file_id: z.string(),
});

export const readFileResponseSchema = fileSchema;

export const deleteFileRequestSchema = z.object({
  context_id: z.string().nullable(),
  file_id: z.string(),
});

export const deleteFileResponseSchema = z.null();

export const readFileContentRequestSchema = z.object({
  context_id: z.string().nullable(),
  file_id: z.string(),
});

export const readFileContentResponseSchema = z.unknown();

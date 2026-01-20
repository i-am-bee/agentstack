/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

export const errorSchema = z.object({
  title: z.string(),
  message: z.string(),
});

export const errorGroupSchema = z.object({
  message: z.string(),
  errors: z.array(errorSchema),
});

export const errorMetadataSchema = z.object({
  error: z.union([errorSchema, errorGroupSchema]),
  context: z.record(z.string(), z.unknown()).nullish(),
  stack_trace: z.string().nullish(),
});

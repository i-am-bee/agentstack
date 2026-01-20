/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

export const citationSchema = z.object({
  url: z.string().nullish(),
  start_index: z.number().nullish(),
  end_index: z.number().nullish(),
  title: z.string().nullish(),
  description: z.string().nullish(),
});

export const citationMetadataSchema = z.object({
  citations: z.array(citationSchema),
});

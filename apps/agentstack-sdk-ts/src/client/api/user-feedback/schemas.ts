/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

export const createUserFeedbackRequestSchema = z.object({
  provider_id: z.string(),
  context_id: z.string(),
  task_id: z.string(),
  message: z.string(),
  rating: z.union([z.literal(1), z.literal(-1)]),
  comment: z.string().nullish(),
  comment_tags: z.array(z.string()).nullish(),
});

export const createUserFeedbackResponseSchema = z.null();

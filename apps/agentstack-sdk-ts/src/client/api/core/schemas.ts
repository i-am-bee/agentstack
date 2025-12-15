/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

export const paginationQuerySchema = z.object({
  limit: z.number().optional(),
  order: z.string().optional(),
  order_by: z.string().optional(),
  page_token: z.string().nullish(),
});

export const paginatedResponseSchema = z.object({
  items: z.array(z.unknown()),
  total_count: z.number(),
  has_more: z.boolean(),
  next_page_token: z.string().nullable(),
});

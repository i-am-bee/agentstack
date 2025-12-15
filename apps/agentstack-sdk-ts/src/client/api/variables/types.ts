/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type z from 'zod';

import type {
  listVariablesRequestSchema,
  listVariablesResponseSchema,
  updateVariablesRequestSchema,
  updateVariablesResponseSchema,
} from './schemas';

export type ListVariablesRequest = z.infer<typeof listVariablesRequestSchema>;
export type ListVariablesResponse = z.infer<typeof listVariablesResponseSchema>;

export type UpdateVariablesRequest = z.infer<typeof updateVariablesRequestSchema>;
export type UpdateVariablesResponse = z.infer<typeof updateVariablesResponseSchema>;

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

export const listVariablesRequestSchema = z.never();

export const listVariablesResponseSchema = z.object({
  variables: z.record(z.string(), z.string()),
});

export const updateVariablesRequestSchema = z.object({
  variables: z.record(z.string(), z.union([z.string(), z.null()])),
});

export const updateVariablesResponseSchema = z.null();

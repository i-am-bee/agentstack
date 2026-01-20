/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

export const systemConfigurationSchema = z.object({
  id: z.string(),
  created_by: z.string(),
  updated_at: z.string(),
  default_embedding_model: z.string().nullish(),
  default_llm_model: z.string().nullish(),
});

export const readSystemConfigurationRequestSchema = z.never();

export const readSystemConfigurationResponseSchema = systemConfigurationSchema;

export const updateSystemConfigurationRequestSchema = z.object({
  default_embedding_model: z.string().nullish(),
  default_llm_model: z.string().nullish(),
});

export const updateSystemConfigurationResponseSchema = systemConfigurationSchema;

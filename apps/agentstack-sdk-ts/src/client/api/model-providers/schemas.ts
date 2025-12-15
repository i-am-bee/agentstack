/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

import { paginatedResponseSchema } from '../core/schemas';
import { ModelCapability, ModelProviderType } from './types';

export const modelCapabilitySchema = z.enum(ModelCapability);

export const modelProviderTypeSchema = z.enum(ModelProviderType);

export const modelProviderSchema = z.object({
  id: z.string(),
  base_url: z.string(),
  created_at: z.string(),
  capabilities: z.array(modelCapabilitySchema),
  name: z.string().nullish(),
  description: z.string().nullish(),
  type: modelProviderTypeSchema,
});

export const listModelProvidersRequestSchema = z.never();

export const listModelProvidersResponseSchema = paginatedResponseSchema.extend({
  items: z.array(modelProviderSchema),
});

export const createModelProviderRequestSchema = z.object({
  api_key: z.string(),
  base_url: z.string(),
  type: modelProviderTypeSchema,
  name: z.string().nullish(),
  description: z.string().nullish(),
  watsonx_project_id: z.string().nullish(),
  watsonx_space_id: z.string().nullish(),
});

export const createModelProviderResponseSchema = modelProviderSchema;

export const readModelProviderRequestSchema = z.object({
  model_provider_id: z.string(),
});

export const readModelProviderResponseSchema = modelProviderSchema;

export const deleteModelProviderRequestSchema = z.object({
  model_provider_id: z.string(),
});

export const deleteModelProviderResponseSchema = z.null();

export const matchModelProvidersRequestSchema = z.object({
  suggested_models: z.array(z.string()).nullable(),
  capability: modelCapabilitySchema,
  score_cutoff: z.number(),
});

export const matchModelProvidersResponseSchema = paginatedResponseSchema.extend({
  items: z.array(
    z.object({
      model_id: z.string(),
      score: z.number(),
    }),
  ),
});

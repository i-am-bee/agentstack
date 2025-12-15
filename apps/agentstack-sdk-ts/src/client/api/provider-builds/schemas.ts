/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

import { dockerImageIdSchema, readableStreamSchema, resolvedGitHubUrlSchema } from '../../api/common/schemas';
import { paginatedResponseSchema, paginationQuerySchema } from '../core/schemas';
import { ProviderBuildState } from './types';

export const providerBuildStateSchema = z.enum(ProviderBuildState);

export const providerBuildAddActionSchema = z.object({
  type: z.literal('add_provider'),
  auto_stop_timeout_sec: z.number().nullish(),
  variables: z.record(z.string(), z.string()).nullish(),
});

export const providerBuildUpdateActionSchema = z.object({
  type: z.literal('update_provider'),
  provider_id: z.string(),
});

export const providerBuildNoActionSchema = z.object({
  type: z.literal('no_action'),
});

export const providerBuildOnCompleteActionSchema = z.union([
  providerBuildAddActionSchema,
  providerBuildUpdateActionSchema,
  providerBuildNoActionSchema,
]);

export const providerBuildConfigurationSchema = z.object({
  dockerfile_path: z.string().nullish(),
});

export const providerBuildSchema = z.object({
  id: z.string(),
  created_at: z.string(),
  created_by: z.string(),
  provider_origin: z.string(),
  status: providerBuildStateSchema,
  source: resolvedGitHubUrlSchema,
  destination: dockerImageIdSchema,
  on_complete: providerBuildOnCompleteActionSchema,
  build_configuration: providerBuildConfigurationSchema.nullish(),
  provider_id: z.string().nullish(),
  error_message: z.string().nullish(),
});

export const listProviderBuildsRequestSchema = z.object({
  query: paginationQuerySchema
    .extend({
      status: providerBuildStateSchema.nullish(),
      user_owned: z.boolean().nullish(),
    })
    .optional(),
});

export const listProviderBuildsResponseSchema = paginatedResponseSchema.extend({
  items: z.array(providerBuildSchema),
});

export const createProviderBuildRequestSchema = z.object({
  location: z.string(),
  build_configuration: providerBuildConfigurationSchema.nullish(),
  on_complete: providerBuildOnCompleteActionSchema.optional(),
});

export const createProviderBuildResponseSchema = providerBuildSchema;

export const readProviderBuildRequestSchema = z.object({
  id: z.string(),
});

export const readProviderBuildResponseSchema = providerBuildSchema;

export const deleteProviderBuildRequestSchema = z.object({
  id: z.string(),
});

export const deleteProviderBuildResponseSchema = z.null();

export const readProviderBuildLogsRequestSchema = z.object({
  id: z.string(),
});

export const readProviderBuildLogsResponseSchema = readableStreamSchema;

export const previewProviderBuildRequestSchema = z.object({
  location: z.string(),
  build_configuration: providerBuildConfigurationSchema.nullish(),
  on_complete: providerBuildOnCompleteActionSchema.optional(),
});

export const previewProviderBuildResponseSchema = providerBuildSchema;

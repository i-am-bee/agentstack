/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

import { agentCardSchema } from '../../a2a/protocol/schemas';
import {
  dockerImageProviderLocationSchema,
  fileSystemRegistryLocationSchema,
  gitHubRegistryLocationSchema,
  networkProviderLocationSchema,
  networkRegistryLocationSchema,
  readableStreamSchema,
  resolvedDockerImageIdSchema,
  resolvedGitHubUrlSchema,
} from '../common/schemas';
import { paginatedResponseSchema } from '../core/schemas';
import { ProviderStatus, ProviderType, ProviderUnmanagedStatus } from './types';

export const providerTypeSchema = z.enum(ProviderType);

export const providerStatusSchema = z.enum(ProviderStatus);

export const providerUnmanagedStatusSchema = z.enum(ProviderUnmanagedStatus);

export const providerErrorSchema = z.object({
  message: z.string(),
});

export const providerEnvVarSchema = z.object({
  name: z.string(),
  required: z.boolean(),
  description: z.string().nullish(),
});

export const providerVersionInfoSchema = z.object({
  docker: resolvedDockerImageIdSchema.nullish(),
  github: resolvedGitHubUrlSchema.nullish(),
});

export const providerSchema = z.object({
  id: z.string(),
  source: z.union([dockerImageProviderLocationSchema, networkProviderLocationSchema]),
  agent_card: agentCardSchema,
  state: z.union([providerStatusSchema, providerUnmanagedStatusSchema]),
  origin: z.string(),
  created_at: z.string(),
  created_by: z.string(),
  updated_at: z.string(),
  last_active_at: z.string(),
  auto_stop_timeout: z.string(),
  managed: z.boolean(),
  type: providerTypeSchema,
  env: z.array(providerEnvVarSchema),
  registry: z
    .union([gitHubRegistryLocationSchema, networkRegistryLocationSchema, fileSystemRegistryLocationSchema])
    .nullish(),
  last_error: providerErrorSchema.nullish(),
  missing_configuration: z.array(providerEnvVarSchema).optional(),
  version_info: providerVersionInfoSchema.optional(),
});

export const listProvidersRequestSchema = z.object({
  query: z
    .object({
      origin: z.string().nullish(),
      user_owned: z.boolean().nullish(),
    })
    .optional(),
});

export const listProvidersResponseSchema = paginatedResponseSchema.extend({
  items: z.array(providerSchema),
});

export const createProviderRequestSchema = z.object({
  location: z.union([dockerImageProviderLocationSchema, networkProviderLocationSchema]),
  agent_card: agentCardSchema.nullish(),
  auto_stop_timeout_sec: z.number().nullish(),
  origin: z.string().nullish(),
  variables: z.record(z.string(), z.string()).nullish(),
});

export const createProviderResponseSchema = providerSchema;

export const readProviderRequestSchema = z.object({
  id: z.string(),
});

export const readProviderResponseSchema = providerSchema;

export const deleteProviderRequestSchema = z.object({
  id: z.string(),
});

export const deleteProviderResponseSchema = z.null();

export const patchProviderRequestSchema = z.object({
  id: z.string(),
  location: z.union([dockerImageProviderLocationSchema, networkProviderLocationSchema]).nullish(),
  agent_card: agentCardSchema.nullish(),
  auto_stop_timeout_sec: z.number().nullish(),
  origin: z.string().nullish(),
  variables: z.record(z.string(), z.string()).nullish(),
});

export const patchProviderResponseSchema = providerSchema;

export const readProviderLogsRequestSchema = z.object({
  id: z.string(),
});

export const readProviderLogsResponseSchema = readableStreamSchema;

export const listProviderVariablesRequestSchema = z.object({
  id: z.string(),
});

export const listProviderVariablesResponseSchema = z.object({
  variables: z.record(z.string(), z.string()),
});

export const updateProviderVariablesRequestSchema = z.object({
  id: z.string(),
  variables: z.record(z.string(), z.union([z.string(), z.null()])),
});

export const updateProviderVariablesResponseSchema = z.null();

export const readProviderByLocationRequestSchema = z.object({
  location: z.string(),
});

export const readProviderByLocationResponseSchema = providerSchema;

export const previewProviderRequestSchema = createProviderRequestSchema;

export const previewProviderResponseSchema = providerSchema;

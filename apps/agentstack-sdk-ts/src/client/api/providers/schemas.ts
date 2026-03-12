/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

import { agentCardSchema } from '../../a2a/protocol/schemas';
import { networkProviderLocationSchema, readableStreamSchema } from '../common/schemas';
import { paginatedResponseSchema } from '../core/schemas';
import { ProviderState } from './types';

export const providerStateSchema = z.enum(ProviderState);

export const providerErrorSchema = z.object({
  message: z.string(),
});

export const providerEnvVarSchema = z.object({
  name: z.string(),
  required: z.boolean(),
  description: z.string().nullish(),
});

export const providerSchema = z.object({
  id: z.string(),
  source: networkProviderLocationSchema,
  source_type: z.string().optional(),
  agent_card: agentCardSchema,
  state: providerStateSchema,
  origin: z.string(),
  created_at: z.string(),
  created_by: z.string(),
  updated_at: z.string(),
  last_active_at: z.string(),
  last_error: providerErrorSchema.nullish(),
  missing_configuration: z.array(providerEnvVarSchema).optional(),
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
  location: networkProviderLocationSchema,
  agent_card: agentCardSchema.nullish(),
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
  location: networkProviderLocationSchema.nullish(),
  agent_card: agentCardSchema.nullish(),
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

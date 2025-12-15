/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type z from 'zod';

import type {
  createProviderBuildRequestSchema,
  createProviderBuildResponseSchema,
  deleteProviderBuildRequestSchema,
  deleteProviderBuildResponseSchema,
  listProviderBuildsRequestSchema,
  listProviderBuildsResponseSchema,
  previewProviderBuildRequestSchema,
  previewProviderBuildResponseSchema,
  providerBuildAddActionSchema,
  providerBuildConfigurationSchema,
  providerBuildNoActionSchema,
  providerBuildOnCompleteActionSchema,
  providerBuildSchema,
  providerBuildUpdateActionSchema,
  readProviderBuildLogsRequestSchema,
  readProviderBuildLogsResponseSchema,
  readProviderBuildRequestSchema,
  readProviderBuildResponseSchema,
} from './schemas';

export enum ProviderBuildState {
  Missing = 'missing',
  InProgress = 'in_progress',
  BuildCompleted = 'build_completed',
  Completed = 'completed',
  Failed = 'failed',
}

export type ProviderBuildAddAction = z.infer<typeof providerBuildAddActionSchema>;
export type ProviderBuildUpdateAction = z.infer<typeof providerBuildUpdateActionSchema>;
export type ProviderBuildNoAction = z.infer<typeof providerBuildNoActionSchema>;
export type ProviderBuildOnCompleteAction = z.infer<typeof providerBuildOnCompleteActionSchema>;
export type ProviderBuildConfiguration = z.infer<typeof providerBuildConfigurationSchema>;

export type ProviderBuild = z.infer<typeof providerBuildSchema>;

export type ListProviderBuildsRequest = z.infer<typeof listProviderBuildsRequestSchema>;
export type ListProviderBuildsResponse = z.infer<typeof listProviderBuildsResponseSchema>;

export type CreateProviderBuildRequest = z.infer<typeof createProviderBuildRequestSchema>;
export type CreateProviderBuildResponse = z.infer<typeof createProviderBuildResponseSchema>;

export type ReadProviderBuildRequest = z.infer<typeof readProviderBuildRequestSchema>;
export type ReadProviderBuildResponse = z.infer<typeof readProviderBuildResponseSchema>;

export type DeleteProviderBuildRequest = z.infer<typeof deleteProviderBuildRequestSchema>;
export type DeleteProviderBuildResponse = z.infer<typeof deleteProviderBuildResponseSchema>;

export type ReadProviderBuildLogsRequest = z.infer<typeof readProviderBuildLogsRequestSchema>;
export type ReadProviderBuildLogsResponse = z.infer<typeof readProviderBuildLogsResponseSchema>;

export type PreviewProviderBuildRequest = z.infer<typeof previewProviderBuildRequestSchema>;
export type PreviewProviderBuildResponse = z.infer<typeof previewProviderBuildResponseSchema>;

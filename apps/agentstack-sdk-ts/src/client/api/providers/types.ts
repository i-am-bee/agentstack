/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type z from 'zod';

import type {
  createProviderRequestSchema,
  createProviderResponseSchema,
  deleteProviderRequestSchema,
  deleteProviderResponseSchema,
  listProvidersRequestSchema,
  listProvidersResponseSchema,
  listProviderVariablesRequestSchema,
  listProviderVariablesResponseSchema,
  patchProviderRequestSchema,
  patchProviderResponseSchema,
  previewProviderRequestSchema,
  previewProviderResponseSchema,
  providerEnvVarSchema,
  providerErrorSchema,
  providerSchema,
  providerVersionInfoSchema,
  readProviderByLocationRequestSchema,
  readProviderByLocationResponseSchema,
  readProviderLogsRequestSchema,
  readProviderLogsResponseSchema,
  readProviderRequestSchema,
  readProviderResponseSchema,
  updateProviderVariablesRequestSchema,
  updateProviderVariablesResponseSchema,
} from './schemas';

export enum ProviderType {
  Managed = 'managed',
  Unmanaged = 'unmanaged',
}

export enum ProviderStatus {
  Missing = 'missing',
  Starting = 'starting',
  Ready = 'ready',
  Running = 'running',
  Error = 'error',
}

export enum ProviderUnmanagedStatus {
  Online = 'online',
  Offline = 'offline',
}

export type ProviderError = z.infer<typeof providerErrorSchema>;
export type ProviderEnvVar = z.infer<typeof providerEnvVarSchema>;
export type ProviderVersionInfo = z.infer<typeof providerVersionInfoSchema>;

export type Provider = z.infer<typeof providerSchema>;

export type ListProvidersRequest = z.infer<typeof listProvidersRequestSchema>;
export type ListProvidersResponse = z.infer<typeof listProvidersResponseSchema>;

export type CreateProviderRequest = z.infer<typeof createProviderRequestSchema>;
export type CreateProviderResponse = z.infer<typeof createProviderResponseSchema>;

export type ReadProviderRequest = z.infer<typeof readProviderRequestSchema>;
export type ReadProviderResponse = z.infer<typeof readProviderResponseSchema>;

export type DeleteProviderRequest = z.infer<typeof deleteProviderRequestSchema>;
export type DeleteProviderResponse = z.infer<typeof deleteProviderResponseSchema>;

export type PatchProviderRequest = z.infer<typeof patchProviderRequestSchema>;
export type PatchProviderResponse = z.infer<typeof patchProviderResponseSchema>;

export type ReadProviderLogsRequest = z.infer<typeof readProviderLogsRequestSchema>;
export type ReadProviderLogsResponse = z.infer<typeof readProviderLogsResponseSchema>;

export type ListProviderVariablesRequest = z.infer<typeof listProviderVariablesRequestSchema>;
export type ListProviderVariablesResponse = z.infer<typeof listProviderVariablesResponseSchema>;

export type UpdateProviderVariablesRequest = z.infer<typeof updateProviderVariablesRequestSchema>;
export type UpdateProviderVariablesResponse = z.infer<typeof updateProviderVariablesResponseSchema>;

export type ReadProviderByLocationRequest = z.infer<typeof readProviderByLocationRequestSchema>;
export type ReadProviderByLocationResponse = z.infer<typeof readProviderByLocationResponseSchema>;

export type PreviewProviderRequest = z.infer<typeof previewProviderRequestSchema>;
export type PreviewProviderResponse = z.infer<typeof previewProviderResponseSchema>;

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { z } from 'zod';

import type { ContextPermissionsGrant, GlobalPermissionsGrant, ModelCapability } from './types';
import { contextSchema, contextTokenSchema, modelProviderMatchSchema } from './types';

export interface MatchProvidersParams {
  suggestedModels: string[] | null;
  capability: ModelCapability;
  scoreCutoff: number;
}

export interface CreateContextTokenParams {
  contextId: string;
  globalPermissions: GlobalPermissionsGrant;
  contextPermissions: ContextPermissionsGrant;
}

export const buildApiClient = (
  {
    baseUrl,
    fetch: customFetchImpl,
  }: {
    baseUrl: string;
    fetch?: typeof globalThis.fetch;
  } = { baseUrl: '' },
) => {
  const maybeFetchFn = customFetchImpl ?? (typeof globalThis.fetch !== 'undefined' ? globalThis.fetch : undefined);

  if (!maybeFetchFn) {
    throw new Error(
      'fetch is not available. In Node.js < 18 or environments without global fetch, ' +
        'provide a fetch implementation via the fetch option.',
    );
  }

  const fetchFn = maybeFetchFn;

  async function callApi<T>(method: 'POST', url: string, data: Record<string, unknown>, resultSchema: z.ZodSchema<T>) {
    const response = await fetchFn(`${baseUrl}${url}`, {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      throw new Error(`Failed to call Agent Stackk API - ${url}`);
    }

    const json = await response.json();
    return resultSchema.parse(json);
  }

  const createContext = async (providerId: string) =>
    await callApi('POST', '/api/v1/contexts', { metadata: {}, provider_id: providerId }, contextSchema);

  const createContextToken = async ({ contextId, globalPermissions, contextPermissions }: CreateContextTokenParams) => {
    const token = await callApi(
      'POST',
      `/api/v1/contexts/${contextId}/token`,
      {
        grant_global_permissions: globalPermissions,
        grant_context_permissions: contextPermissions,
      },
      contextTokenSchema,
    );

    return { token, contextId };
  };

  const matchProviders = async ({ suggestedModels, capability, scoreCutoff }: MatchProvidersParams) => {
    return await callApi(
      'POST',
      '/api/v1/model_providers/match',
      {
        capability,
        score_cutoff: scoreCutoff,
        suggested_models: suggestedModels,
      },
      modelProviderMatchSchema,
    );
  };

  return { createContextToken, createContext, matchProviders };
};

export type AgentstackClient = ReturnType<typeof buildApiClient>;

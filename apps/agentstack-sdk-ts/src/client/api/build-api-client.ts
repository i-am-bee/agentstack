/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { z } from 'zod';
import { contextSchema, contextTokenSchema, ModelCapability, modelProviderMatchSchema } from './types';

export const buildApiClient = ({ baseUrl }: { baseUrl: string } = { baseUrl: '' }) => {
  async function callApi<T>(
    method: 'POST' | 'GET',
    url: string,
    data: Record<string, unknown>,
    resultSchema: z.ZodSchema<T>,
  ) {
    const response = await fetch(`${baseUrl}${url}`, {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      throw new Error('Failed to get context token.');
    }
    const json = await response.json();
    return resultSchema.parse(json);
  }

  const createContext = async (providerId: string) => {
    const { id: contextId } = await callApi(
      'POST',
      '/api/v1/contexts',
      { metadata: {}, provider_id: providerId },
      contextSchema,
    );

    return contextId;
  };

  const createContextToken = async (contextId: string) => {
    const token = await callApi(
      'POST',
      `/api/v1/contexts/${contextId}/token`,
      {
        context_id: contextId,
        grant_global_permissions: {
          llm: ['*'],
          a2a_proxy: [],
          contexts: [],
          embeddings: ['*'],
          feedback: [],
          files: [],
          providers: [],
          provider_variables: [],
          model_providers: [],
          mcp_providers: [],
          mcp_proxy: [],
          mcp_tools: [],
          vector_stores: [],
          context_data: [],
        },
        grant_context_permissions: {
          files: ['*'],
          vector_stores: ['*'],
          context_data: ['*'],
        },
      },
      contextTokenSchema,
    );

    return { token, contextId };
  };

  const matchProviders = async (suggestedModels: string[], capability: ModelCapability, scoreCutoff: number) => {
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

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQuery } from '@tanstack/react-query';
import { useEffect } from 'react';

import type { EmbeddingDemand } from '#api/a2a/extensions/services/embedding.ts';
import type { LLMDemand } from '#api/a2a/extensions/services/llm.ts';
import { useApp } from '#contexts/App/index.ts';
import { ModelCapability } from '#modules/platform-context/types.ts';

import { matchProviders } from '..';

const MAX_PROVIDERS = 5;

type MatchProvidersResult = Record<string, string[]>;

export function useMatchEmbeddingProviders(
  demands: EmbeddingDemand['embedding_demands'],
  onSuccess: (data: MatchProvidersResult) => void,
) {
  const { featureFlags } = useApp();
  const demandKey = Object.entries(demands)
    .map(([key, value]) => [key, ...(value.suggested ?? [])])
    .join();

  const query = useQuery({
    queryKey: ['matchEmbeddingProviders', demandKey],
    enabled: featureFlags.ModelProviders && Object.keys(demands).length > 0,
    queryFn: async () => {
      const demandKeys = Object.keys(demands);

      const allProviders = await Promise.all(
        demandKeys.map(async (demandKey) => {
          const result = await matchProviders(demands[demandKey].suggested ?? [], ModelCapability.EMBEDDING);
          return {
            key: demandKey,
            providers: result?.items.map((item) => item.model_id).slice(0, MAX_PROVIDERS) ?? [],
          };
        }),
      );

      return allProviders.reduce<MatchProvidersResult>((acc, { key, providers }) => {
        acc[key] = providers;
        return acc;
      }, {});
    },
  });

  const { isSuccess, data } = query;

  useEffect(() => {
    if (isSuccess && data) {
      onSuccess(data);
    }
  }, [isSuccess, data, onSuccess]);

  return query;
}

export function useMatchLLMProviders(
  demands: LLMDemand['llm_demands'],
  onSuccess: (data: MatchProvidersResult) => void,
) {
  const { featureFlags } = useApp();
  const demandKey = Object.entries(demands)
    .map(([key, value]) => [key, ...(value.suggested ?? [])])
    .join();

  const query = useQuery({
    queryKey: ['matchLLMProviders', demandKey],
    enabled: featureFlags.ModelProviders && Object.keys(demands).length > 0,
    queryFn: async () => {
      const demandKeys = Object.keys(demands);

      const allProviders = await Promise.all(
        demandKeys.map(async (demandKey) => {
          const result = await matchProviders(demands[demandKey].suggested ?? [], ModelCapability.LLM);
          return {
            key: demandKey,
            providers: result?.items.map((item) => item.model_id).slice(0, MAX_PROVIDERS) ?? [],
          };
        }),
      );

      return allProviders.reduce<MatchProvidersResult>((acc, { key, providers }) => {
        acc[key] = providers;
        return acc;
      }, {});
    },
  });

  const { isSuccess, data } = query;

  useEffect(() => {
    if (isSuccess && data) {
      onSuccess(data);
    }
  }, [isSuccess, data, onSuccess]);

  return query;
}

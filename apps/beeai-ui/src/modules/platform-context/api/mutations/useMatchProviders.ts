/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQuery } from '@tanstack/react-query';
import type { EmbeddingDemand, LLMDemand } from 'beeai-sdk';
import { useEffect } from 'react';

import { useApp } from '#contexts/App/index.ts';
import { ModelCapability } from '#modules/platform-context/types.ts';

import { matchProviders } from '..';

const MAX_PROVIDERS = 5;

type MatchProvidersResult = Record<string, string[]>;

interface Props {
  demands: EmbeddingDemand['embedding_demands'] | LLMDemand['llm_demands'];
  onSuccess: (data: MatchProvidersResult) => void;
  capability: ModelCapability;
}

export function useMatchProviders({ demands, onSuccess, capability }: Props) {
  const {
    config: { featureFlags, isAuthEnabled },
  } = useApp();

  const demandKey = Object.entries(demands)
    .map(([key, value]) => [key, ...(value.suggested ?? [])])
    .join();

  const query = useQuery({
    queryKey: [capability === ModelCapability.Embedding ? 'matchEmbeddingProviders' : 'matchLLMProviders', demandKey],
    enabled: featureFlags.ModelProviders && Object.keys(demands).length > 0,
    queryFn: async () => {
      const demandKeys = Object.keys(demands);

      const allProviders = await Promise.all(
        demandKeys.map(async (demandKey) => {
          const result = await matchProviders({
            suggested_models: demands[demandKey].suggested ?? [],
            capability,
          });
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
    meta: {
      errorToast: {
        title: 'Model providers query failed',
        message: !isAuthEnabled ? 'Have you configured providers by running `beeai model setup`?' : undefined,
        includeErrorMessage: true,
      },
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

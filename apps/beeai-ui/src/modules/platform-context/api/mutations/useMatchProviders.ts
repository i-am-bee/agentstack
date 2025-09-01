/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQuery } from '@tanstack/react-query';
import { useEffect } from 'react';

import type { LLMDemand } from '#api/a2a/extensions/services/llm.ts';

import { matchProviders } from '..';

const MAX_PROVIDERS = 5;

export function useMatchProviders(
  demands: LLMDemand['llm_demands'],
  onSuccess: (data: Record<string, string[]>) => void,
) {
  const demandKey = Object.entries(demands)
    .map(([key, value]) => [key, ...(value.suggested ?? [])])
    .join();

  const query = useQuery({
    queryKey: ['matchProviders', demandKey],
    queryFn: async () => {
      const acc: Record<string, string[]> = {};

      for (const demandKey in demands) {
        const result = await matchProviders(demands[demandKey].suggested ?? []);
        acc[demandKey] = result?.items.map((item) => item.model_id).filter((_, index) => index < MAX_PROVIDERS) ?? [];
      }

      return acc;
    },
  });

  useEffect(() => {
    if (query.isSuccess && query.data) {
      onSuccess(query.data);
    }
  }, [query.isSuccess, query.data, onSuccess]);

  return query;
}

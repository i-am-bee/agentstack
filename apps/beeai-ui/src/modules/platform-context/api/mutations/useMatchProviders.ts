/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQuery } from '@tanstack/react-query';

import type { LLMDemand } from '#api/a2a/extensions/services/llm.ts';

import { matchProviders } from '..';

export function useMatchProviders(demands: LLMDemand) {
  // TODO: more
  const mutation = useQuery({
    queryKey: ['matchProviders'],
    queryFn: async () => {
      const acc = {};
      for (const demandKey in demands.llm_demands) {
        const result = await matchProviders(demands.llm_demands[demandKey].suggested ?? []);
        acc[demandKey] = result?.items.map((item) => item.model_id).filter((_, index) => index < 5) ?? [];
      }

      return acc;
    },
  });

  return mutation;
}

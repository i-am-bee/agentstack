/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQuery } from '@tanstack/react-query';

import { buildAgent } from '#modules/agents/utils.ts';
import { listProviders } from '#modules/providers/api/index.ts';

import { agentKeys } from '../keys';

export function useAgent({ providerId }: { providerId: string }) {
  return useQuery({
    queryKey: agentKeys.list(),
    // TODO: We could read agent via its provider id, but currently we are loading
    // all the providers anyway, so we can reuse the data here
    queryFn: listProviders,
    select: (response) => {
      const agentProvider = response?.items.find(({ id }) => id === providerId);
      return agentProvider ? buildAgent(agentProvider) : undefined;
    },
  });
}

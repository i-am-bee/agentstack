/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQuery } from '@tanstack/react-query';

import { buildAgent, isAgentUiSupported, sortAgentsByName, sortProvidersByCreatedAt } from '#modules/agents/utils.ts';
import { listProviders } from '#modules/providers/api/index.ts';
import { providerKeys } from '#modules/providers/api/keys.ts';

interface Props {
  onlyUiSupported?: boolean;
  orderBy?: 'name' | 'createdAt';
}

export function useListAgents({ onlyUiSupported, orderBy }: Props = {}) {
  const query = useQuery({
    queryKey: providerKeys.list(),
    queryFn: () => listProviders(),
    select: (response) => {
      let items = response?.items ?? [];

      if (orderBy === 'createdAt') {
        items = items.sort(sortProvidersByCreatedAt);
      }

      let agents = items.map(buildAgent);

      if (onlyUiSupported) {
        agents = agents.filter(isAgentUiSupported);
      }

      if (orderBy === 'name') {
        agents = agents.sort(sortAgentsByName);
      }

      return agents;
    },
    refetchInterval: 30_000,
  });

  return query;
}

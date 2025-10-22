/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQuery } from '@tanstack/react-query';

import { buildAgent, isAgentUiSupported, sortAgentsByName, sortProvidersBy } from '#modules/agents/utils.ts';
import { listProviders } from '#modules/providers/api/index.ts';
import { providerKeys } from '#modules/providers/api/keys.ts';
import type { ListProvidersParams, ListProvidersResponse } from '#modules/providers/api/types.ts';

import { ListAgentsOrderBy } from '../types';

interface Props extends ListProvidersParams {
  onlyUiSupported?: boolean;
  orderBy?: ListAgentsOrderBy;
  initialData?: ListProvidersResponse;
}

export function useListAgents({ onlyUiSupported, orderBy, initialData, ...params }: Props = {}) {
  const query = useQuery({
    queryKey: providerKeys.list(params),
    queryFn: () => listProviders(params),
    select: (response) => {
      let items = response?.items ?? [];

      if (orderBy === ListAgentsOrderBy.CreatedAt || orderBy === ListAgentsOrderBy.LastActiveAt) {
        items = items.sort((...params) => sortProvidersBy(...params, orderBy));
      }

      let agents = items.map(buildAgent);

      if (onlyUiSupported) {
        agents = agents.filter(isAgentUiSupported);
      }

      if (orderBy === ListAgentsOrderBy.Name) {
        agents = agents.sort(sortAgentsByName);
      }

      return agents;
    },
    refetchInterval: 30_000,
    initialData,
  });

  return query;
}

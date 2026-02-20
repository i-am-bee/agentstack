/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQuery } from '@tanstack/react-query';
import {
  type ListProvidersRequest,
  type ListProvidersResponse,
  ProviderStatus,
  ProviderUnmanagedStatus,
} from 'agentstack-sdk';

import { buildAgent, isAgentUiSupported, sortAgentsByName, sortProvidersBy } from '#modules/agents/utils.ts';
import { listProviders } from '#modules/providers/api/index.ts';
import { providerKeys } from '#modules/providers/api/keys.ts';

import { ListAgentsOrderBy } from '../types';

interface Props extends ListProvidersRequest {
  includeUnsupportedUi?: boolean;
  includeOffline?: boolean;
  orderBy?: ListAgentsOrderBy;
  initialData?: ListProvidersResponse;
}

export function useListAgents({ includeUnsupportedUi, includeOffline, orderBy, initialData, ...request }: Props = {}) {
  const query = useQuery({
    queryKey: providerKeys.list(request),
    queryFn: () => listProviders(request),
    select: (response) => {
      let items = response?.items ?? [];

      if (orderBy === ListAgentsOrderBy.CreatedAt || orderBy === ListAgentsOrderBy.LastActiveAt) {
        items = items.sort((...providers) => sortProvidersBy(...providers, orderBy));
      }

      if (!includeOffline) {
        items = items.filter(
          ({ state }) => state !== ProviderUnmanagedStatus.Offline && state !== ProviderStatus.Error,
        );
      }

      let agents = items.map(buildAgent);

      if (!includeUnsupportedUi) {
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

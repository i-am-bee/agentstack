/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQuery } from '@tanstack/react-query';

import { buildAgent, isAgentUiSupported, sortAgentsByName } from '#modules/agents/utils.ts';
import { listProviders } from '#modules/providers/api/index.ts';
import { providerKeys } from '#modules/providers/api/keys.ts';

interface Props {
  onlyUiSupported?: boolean;
  sort?: boolean;
}

export function useListAgents({ onlyUiSupported, sort }: Props = {}) {
  const query = useQuery({
    queryKey: providerKeys.list(),
    queryFn: listProviders,
    select: (response) => {
      let agents = response?.items?.map(buildAgent) ?? [];

      if (onlyUiSupported) {
        agents = agents.filter(isAgentUiSupported);
      }

      if (sort) {
        agents = agents.sort(sortAgentsByName);
      }

      return agents;
    },
    refetchInterval: 30_000,
  });

  return query;
}

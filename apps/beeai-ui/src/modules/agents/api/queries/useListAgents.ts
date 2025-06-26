/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQuery } from '@tanstack/react-query';

import { isAgentUiSupported, sortAgentsByName } from '#modules/agents/utils.ts';

import { listAgents } from '..';
import { agentKeys } from '../keys';
import type { Agent, ListAgentsParams } from '../types';

export function useListAgents({ onlyUiSupported, sort }: ListAgentsParams = {}) {
  const query = useQuery({
    queryKey: agentKeys.list(),
    queryFn: listAgents,
    select: (data) => {
      let agents = data?.agents as Agent[];

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

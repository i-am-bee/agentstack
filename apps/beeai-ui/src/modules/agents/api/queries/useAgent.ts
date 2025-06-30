/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQuery } from '@tanstack/react-query';

import { listAgents } from '..';
import { agentKeys } from '../keys';
import type { Agent, AgentName } from '../types';

export function useAgent({ name }: { name: AgentName }) {
  return useQuery({
    queryKey: agentKeys.list(),
    // TODO: We could use the `acp.agent(name)` endpoint to fetch the exact agent, but currently we are listing
    // all the agents at once, so we can reuse the data here untill the agents have sorting and pagination.
    queryFn: listAgents,
    select: (agents) => {
      const agent = agents.find((item) => name === item.name);

      return agent as Agent;
    },
  });
}

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { useListAgents } from '#modules/agents/api/queries/useListAgents.ts';
import { ListAgentsOrderBy } from '#modules/agents/api/types.ts';
import { AgentCardsList } from '#modules/agents/components/cards/AgentCardsList.tsx';
import type { ListProvidersResponse } from '#modules/providers/api/types.ts';

interface Props {
  initialData?: ListProvidersResponse;
}

export function DiscoverAgentsList({ initialData }: Props) {
  const { data: agents, isLoading } = useListAgents({
    orderBy: ListAgentsOrderBy.Name,
    initialData,
  });

  return (
    <AgentCardsList
      agents={agents}
      isLoading={isLoading}
      heading="Discover agents"
      description="See working agents in action and try them instantly."
    />
  );
}

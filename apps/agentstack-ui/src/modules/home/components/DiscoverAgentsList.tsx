/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { useListAgents } from '#modules/agents/api/queries/useListAgents.ts';
import { ListAgentsOrderBy } from '#modules/agents/api/types.ts';
import { AgentCardsList } from '#modules/agents/components/cards/AgentCardsList.tsx';
import type { ListProvidersResponse } from '#modules/providers/api/types.ts';

import { USER_NOT_OWNED_AGENTS_LIST_PARAMS } from '../constants';

interface Props {
  initialData?: ListProvidersResponse;
}

export function DiscoverAgentsList({ initialData }: Props) {
  const { data: agents, isLoading } = useListAgents({
    ...USER_NOT_OWNED_AGENTS_LIST_PARAMS,
    onlyUiSupported: true,
    orderBy: ListAgentsOrderBy.CreatedAt,
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

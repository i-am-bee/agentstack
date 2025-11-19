/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { AgentCardsList } from '#modules/agents/components/cards/AgentCardsList.tsx';
import type { ListProvidersResponse } from '#modules/providers/api/types.ts';

import { useRecentlyAddedAgents } from '../hooks/useRecentlyAddedAgents';

interface Props {
  initialData?: ListProvidersResponse;
}

export function RecentlyAddedAgentsList({ initialData }: Props) {
  const { data: agents, isLoading } = useRecentlyAddedAgents({ initialData });

  return <AgentCardsList agents={agents} isLoading={isLoading} heading="Recently added by me" />;
}

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { notFound } from 'next/navigation';

import type { Agent } from '#modules/agents/api/types.ts';
import { buildAgent } from '#modules/agents/utils.ts';
import { listProviders } from '#modules/providers/api/index.ts';
import { RunView } from '#modules/runs/components/RunView.tsx';

interface Props {
  searchParams: Promise<{ agent: string }>;
}

export default async function AgentRunPage({ searchParams }: Props) {
  const { agent: agentName } = await searchParams;

  let agent: Agent | undefined;
  try {
    const response = await listProviders();

    const provider = response?.items.find(({ agent_card }) => agent_card.name === decodeURIComponent(agentName));
    if (provider) {
      agent = buildAgent(provider);
    }
  } catch (error) {
    console.error('Error fetching agent:', error);
  }

  if (!agent) {
    notFound();
  }

  return <RunView agent={agent} />;
}

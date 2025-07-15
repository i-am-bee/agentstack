/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { notFound } from 'next/navigation';

import { Agent } from '#modules/agents/api/types.ts';
import { buildAgent } from '#modules/agents/utils.ts';
import { listProviders } from '#modules/providers/api/index.ts';
import { AgentRun } from '#modules/runs/components/AgentRun.tsx';

interface Props {
  params: Promise<{ agentName: string }>;
}

export default async function AgentRunPage({ params }: Props) {
  const { agentName } = await params;

  let agent: Agent | undefined;
  try {
    const response = await listProviders();
    const provider = response?.items.find(({ agent_card }) => agent_card.name === agentName);
    if (provider) {
      agent = buildAgent(provider);
    }
  } catch (error) {
    console.error('Error fetching agent:', error);
  }

  if (!agent) {
    notFound();
  }

  return <AgentRun agent={agent} />;
}

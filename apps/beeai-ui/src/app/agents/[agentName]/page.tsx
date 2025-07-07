/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { notFound } from 'next/navigation';

import { readAgent } from '#modules/agents/api/index.ts';
import { AgentRun } from '#modules/runs/components/AgentRun.tsx';

interface Props {
  params: Promise<{ agentName: string }>;
}

export default async function AgentRunPage({ params }: Props) {
  const { agentName } = await params;

  let agent;
  try {
    agent = await readAgent(agentName);
  } catch (error) {
    console.error('Error fetching agent:', error);
    notFound();
  }

  return <AgentRun agent={agent} />;
}

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { AgentDetail, Container, TryLocallyButton } from '@i-am-bee/beeai-ui';
import { notFound } from 'next/navigation';

import { fetchAgentsList } from '@/api/fetchAgentsList';
import { MainContent } from '@/layouts/MainContent';

interface Props {
  params: Promise<{ name: string }>;
}

export async function generateStaticParams() {
  const agents = await fetchAgentsList();

  return agents.map(({ name }) => ({ name }));
}

export default async function AgentPage({ params }: Props) {
  const { name } = await params;
  const agents = await fetchAgentsList();
  const agent = agents.find((agent) => agent.name === name);

  if (!agent) {
    notFound();
  }

  return (
    <MainContent>
      <Container>
        <AgentDetail agent={agent} buttons={<TryLocallyButton />} />
      </Container>
    </MainContent>
  );
}

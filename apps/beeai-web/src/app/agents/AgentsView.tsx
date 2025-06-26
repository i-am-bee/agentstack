/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';
import { type Agent, AgentCard, AgentsFilters, type AgentsFiltersParams, AgentsList } from '@i-am-bee/beeai-ui';
import { useFormContext } from 'react-hook-form';

import { TransitionLink } from '@/components/TransitionLink/TransitionLink';

interface Props {
  agents: Agent[] | null;
}

export function AgentsView({ agents }: Props) {
  const { watch } = useFormContext<AgentsFiltersParams>();
  const filters = watch();

  return (
    <>
      {agents ? <AgentsFilters agents={agents} /> : <AgentsFilters.Skeleton />}
      <AgentsList agents={agents ?? undefined} filters={filters} isPending={agents == null}>
        {(filteredAgents) =>
          filteredAgents.map((agent, idx) => (
            <li key={idx}>
              <AgentCard key={agent.name} agent={agent} renderTitle={renderAgentTitle} />
            </li>
          ))
        }
      </AgentsList>
    </>
  );
}

interface RenderAgentTitleProps {
  className: string;
  agent: Agent;
}

const renderAgentTitle = ({ className, agent }: RenderAgentTitleProps) => (
  <TransitionLink href={`/agents/${agent.name}`} className={className}>
    {agent.name}
  </TransitionLink>
);

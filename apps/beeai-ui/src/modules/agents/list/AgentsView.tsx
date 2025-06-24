/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useFormContext } from 'react-hook-form';

import { ErrorMessage } from '#components/ErrorMessage/ErrorMessage.tsx';
import { TransitionLink } from '#components/TransitionLink/TransitionLink.tsx';
import { routes } from '#utils/router.ts';

import { useListAgents } from '../api/queries/useListAgents';
import type { Agent } from '../api/types';
import { AgentCard } from '../components/AgentCard';
import { AgentsFilters } from '../components/AgentsFilters';
import { AgentsList } from '../components/AgentsList';
import { ImportAgents } from '../components/ImportAgents';
import type { AgentsFiltersParams } from '../providers/AgentsFiltersProvider';

export function AgentsView() {
  const {
    data: agents,
    isPending,
    error,
    refetch,
    isRefetching,
  } = useListAgents({ onlyUiSupported: true, sort: true });

  const { watch } = useFormContext<AgentsFiltersParams>();
  const filters = watch();

  const renderList = () => {
    if (error && !agents)
      return (
        <ErrorMessage
          title="Failed to load agents."
          onRetry={refetch}
          isRefetching={isRefetching}
          subtitle={error.message}
        />
      );

    return (
      <AgentsList agents={agents} filters={filters} action={<ImportAgents />} isPending={isPending}>
        {(filteredAgents) =>
          filteredAgents?.map((agent, idx) => (
            <li key={idx}>
              <AgentCard
                agent={agent}
                renderTitle={renderAgentTitle}
                // statusIndicator={<AgentStatusIndicator agent={agent} />} we might need this later
              />
            </li>
          ))
        }
      </AgentsList>
    );
  };

  return (
    <>
      {!isPending ? <AgentsFilters agents={agents} /> : <AgentsFilters.Skeleton />}
      {renderList()}
    </>
  );
}

const renderAgentTitle = ({ className, agent }: { className: string; agent: Agent }) => {
  const route = routes.agentDetail({ name: agent.name });
  return (
    <TransitionLink className={className} href={route}>
      {agent.name}
    </TransitionLink>
  );
};

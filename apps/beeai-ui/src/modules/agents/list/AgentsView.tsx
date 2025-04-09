/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
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
// import { ImportAgents } from '../components/ImportAgents';
import type { AgentsFiltersParams } from '../providers/AgentsFiltersProvider';

export function AgentsView() {
  const { data, isPending, error, refetch, isRefetching } = useListAgents();
  const { watch } = useFormContext<AgentsFiltersParams>();
  const filters = watch();

  const renderList = () => {
    if (error && !data)
      return (
        <ErrorMessage
          title="Failed to load agents."
          onRetry={refetch}
          isRefetching={isRefetching}
          subtitle={error.message}
        />
      );

    return (
      // TODO: Agent import feature is temporarily removed as it is broken due to API changes
      // <AgentsList agents={data} filters={filters} action={<ImportAgents />} isPending={isPending}>
      <AgentsList agents={data} filters={filters} isPending={isPending}>
        {(filteredAgents) =>
          filteredAgents?.map((agent, idx) => (
            <li key={idx}>
              <AgentCard agent={agent} renderTitle={renderAgentTitle} />
            </li>
          ))
        }
      </AgentsList>
    );
  };

  return (
    <>
      {!isPending ? <AgentsFilters agents={data} /> : <AgentsFilters.Skeleton />}
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

/**
 * Copyright 2025 IBM Corp.
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

import { ErrorMessage } from '#components/ErrorMessage/ErrorMessage.tsx';
import { TransitionLink } from '#components/TransitionLink/TransitionLink.tsx';
import { routes } from '#utils/router.ts';
import { useFormContext } from 'react-hook-form';
import { useListAgents } from '../api/queries/useListAgents';
import { Agent } from '../api/types';
import { AgentCard } from '../components/AgentCard';
import { AgentsFilters } from '../components/AgentsFilters';
import { AgentsList } from '../components/AgentsList';
import { ImportAgents } from '../components/ImportAgents';
import { AgentsFiltersParams } from '../providers/AgentsFiltersProvider';

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
      <AgentsList agents={data} filters={filters} action={<ImportAgents />} isPending={isPending}>
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
    <TransitionLink className={className} to={route}>
      {agent.name}
    </TransitionLink>
  );
};

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { SkeletonText } from '@carbon/react';
import pluralize from 'pluralize';
import type { ReactNode } from 'react';

import { SkeletonItems } from '#components/SkeletonItems/SkeletonItems.tsx';

import type { Agent } from '../api/types';
import { useFilteredAgents } from '../hooks/useFilteredAgents';
import type { AgentsFiltersParams } from '../providers/AgentsFiltersProvider';
import { AgentCard } from './AgentCard';
import classes from './AgentsList.module.scss';

interface Props {
  agents: Agent[] | undefined;
  filters: AgentsFiltersParams;
  action?: ReactNode;
  isPending: boolean;
  children: (filteredAgents: Agent[]) => ReactNode;
}

export function AgentsList({ agents, filters, action, isPending, children }: Props) {
  const { filteredAgents, filteredCount } = useFilteredAgents({ agents: agents ?? [], filters });
  const totalCount = agents?.length;
  return (
    <div>
      <div className={classes.header}>
        {totalCount == null ? (
          <SkeletonText className={classes.count} width="125px" />
        ) : (
          totalCount > 0 && (
            <p className={classes.count}>
              Showing {totalCount === filteredCount ? totalCount : `${filteredCount} of ${totalCount}`}{' '}
              {pluralize('agent', totalCount)}
            </p>
          )
        )}
        {action}
      </div>

      <ul className={classes.list}>
        {!isPending ? (
          children(filteredAgents)
        ) : (
          <SkeletonItems
            count={5}
            render={(idx) => (
              <li key={idx}>
                <AgentCard.Skeleton />
              </li>
            )}
          />
        )}
      </ul>
    </div>
  );
}

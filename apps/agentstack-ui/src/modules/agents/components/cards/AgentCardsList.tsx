/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { NoItemsMessage } from '#components/NoItemsMessage/NoItemsMessage.tsx';
import { SkeletonItems } from '#components/SkeletonItems/SkeletonItems.tsx';
import { useListAgents } from '#modules/agents/api/queries/useListAgents.ts';

import { AgentCard } from './AgentCard';
import classes from './AgentCardsList.module.scss';

interface Props {
  heading?: string;
}

export function AgentCardsList({ heading }: Props) {
  const { data: agents = [], isLoading } = useListAgents({ onlyUiSupported: true, orderBy: 'createdAt' });

  const noItems = agents.length === 0 && !isLoading;

  return (
    <div className={classes.root}>
      {heading && <h2 className={classes.heading}>{heading}</h2>}

      {noItems ? (
        <NoItemsMessage message="No agent added" />
      ) : (
        <div className={classes.list}>
          {isLoading ? (
            <SkeletonItems count={6} render={(idx) => <AgentCard.Skeleton key={idx} />} />
          ) : (
            agents.map((agent) => <AgentCard agent={agent} key={agent.provider.id} />)
          )}
        </div>
      )}
    </div>
  );
}

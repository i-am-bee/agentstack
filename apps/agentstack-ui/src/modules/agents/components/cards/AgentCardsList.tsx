/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { SkeletonItems } from '#components/SkeletonItems/SkeletonItems.tsx';
import type { Agent } from '#modules/agents/api/types.ts';

import { AgentCard } from './AgentCard';
import classes from './AgentCardsList.module.scss';

interface Props {
  agents: Agent[] | undefined;
  isLoading: boolean;
  heading?: string;
  description?: string;
}

export function AgentCardsList({ heading, description, agents = [], isLoading }: Props) {
  const noItems = agents.length === 0 && !isLoading;

  if (noItems) {
    return null;
  }

  return (
    <section className={classes.root}>
      {(heading || description) && (
        <header className={classes.header}>
          {heading && <h2 className={classes.heading}>{heading}</h2>}

          {description && <p className={classes.description}>{description}</p>}
        </header>
      )}

      <div className={classes.list}>
        {isLoading ? (
          <SkeletonItems count={6} render={(idx) => <AgentCard.Skeleton key={idx} />} />
        ) : (
          agents.map((agent) => <AgentCard agent={agent} key={agent.provider.id} />)
        )}
      </div>
    </section>
  );
}

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { SkeletonText } from '@carbon/react';
import clsx from 'clsx';
import Link from 'next/link';

import type { Agent } from '#modules/agents/api/types.ts';
import { routes } from '#utils/router.ts';

import classes from './AgentCard.module.scss';

interface Props {
  agent: Agent;
}

export function AgentCard({ agent }: Props) {
  const { name, provider, description } = agent;

  return (
    <article className={classes.root}>
      <h3 className={classes.heading}>
        <Link href={routes.agentRun({ providerId: provider.id })} className={classes.link}>
          {name}
        </Link>
      </h3>

      <p className={classes.description}>{description}</p>
    </article>
  );
}

AgentCard.Skeleton = function AgentCardSkeleton() {
  return (
    <article className={clsx(classes.root, classes.skeleton)}>
      <SkeletonText className={classes.heading} />

      <SkeletonText paragraph lineCount={3} className={classes.description} />
    </article>
  );
};

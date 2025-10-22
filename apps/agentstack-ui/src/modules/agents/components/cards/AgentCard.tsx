/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { SkeletonText } from '@carbon/react';
import clsx from 'clsx';
import { formatDistanceToNow } from 'date-fns';
import Link from 'next/link';

import type { Agent } from '#modules/agents/api/types.ts';
import { routes } from '#utils/router.ts';

import classes from './AgentCard.module.scss';

interface Props {
  agent: Agent;
}

export function AgentCard({ agent }: Props) {
  const {
    name,
    provider,
    description,
    provider: { updated_at: updatedAt },
  } = agent;

  return (
    <article className={classes.root}>
      <h3 className={classes.heading}>
        <Link href={routes.agentRun({ providerId: provider.id })} className={classes.link}>
          {name}
        </Link>
      </h3>

      <p className={classes.description}>{description}</p>

      {updatedAt && (
        <div className={classes.footer}>
          <p className={classes.timeAgo}>{getDistance(updatedAt)}</p>
        </div>
      )}
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

function getDistance(date: string) {
  const timeAgo = Date.now() - new Date(date).getTime();

  if (timeAgo < JUST_NOW) {
    return 'Just now';
  }

  return formatDistanceToNow(date, { addSuffix: true })
    .replace(/\b(about|almost|over)\b/g, '')
    .trim();
}

const JUST_NOW = 60_000;

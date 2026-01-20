/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ArrowUpRight } from '@carbon/icons-react';
import { SkeletonText } from '@carbon/react';
import Link from 'next/link';

import type { Agent } from '#modules/agents/api/types.ts';
import { routes } from '#utils/router.ts';

import classes from './AgentsListItem.module.scss';

interface Props {
  agent: Agent;
}

export function AgentsListItem({ agent }: Props) {
  const { name, provider } = agent;

  return (
    <article className={classes.root}>
      <Link
        href={routes.agentRun({ providerId: provider.id })}
        className={classes.link}
        target="_blank"
        rel="noreferrer"
      >
        {name}
        <ArrowUpRight size={LINK_ICON_SIZE} />
      </Link>
    </article>
  );
}

AgentsListItem.Skeleton = function AgentsListItemSkeleton() {
  return (
    <article className={classes.root}>
      <SkeletonText className={classes.link} />
    </article>
  );
};

const LINK_ICON_SIZE = 24;

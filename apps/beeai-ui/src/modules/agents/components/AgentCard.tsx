/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { SkeletonText } from '@carbon/react';
import type { ReactNode } from 'react';

import { MarkdownContent } from '#components/MarkdownContent/MarkdownContent.tsx';
import { TagsList } from '#components/TagsList/TagsList.tsx';

import type { Agent } from '../api/types';
import classes from './AgentCard.module.scss';
import { AgentMetadataView } from './AgentMetadataView';
import { AgentTags } from './AgentTags';
import { BeeBadge } from './BeeBadge';

interface Props {
  agent: Agent;
  renderTitle: (props: { className: string; agent: Agent }) => ReactNode;
  statusIndicator?: ReactNode;
}

export function AgentCard({ agent, renderTitle, statusIndicator }: Props) {
  const { description } = agent;
  return (
    <article className={classes.root}>
      <header className={classes.header}>
        <h2 className={classes.name}>{renderTitle({ className: classes.link, agent })}</h2>

        <BeeBadge agent={agent} />

        {statusIndicator}
      </header>

      <div className={classes.body}>
        <AgentMetadataView agent={agent} />

        {description && <MarkdownContent className={classes.description}>{description}</MarkdownContent>}

        <AgentTags agent={agent} />
      </div>
    </article>
  );
}

AgentCard.Skeleton = function AgentCardSkeleton() {
  return (
    <div className={classes.root}>
      <SkeletonText className={classes.name} width="50%" />

      <div className={classes.body}>
        <AgentMetadataView.Skeleton />

        <div className={classes.description}>
          <SkeletonText paragraph lineCount={2} />
        </div>

        <TagsList.Skeleton length={2} />
      </div>
    </div>
  );
};

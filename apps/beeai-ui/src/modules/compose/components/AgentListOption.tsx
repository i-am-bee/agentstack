/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { SkeletonText } from '@carbon/react';
import clsx from 'clsx';
import type { MouseEvent } from 'react';

import { TagsList } from '#components/TagsList/TagsList.tsx';
import type { Agent } from '#modules/agents/api/types.ts';
import { AgentTags } from '#modules/agents/components/AgentTags.tsx';
import { BeeBadge } from '#modules/agents/components/BeeBadge.tsx';
import { getAgentUiMetadata } from '#modules/agents/utils.ts';

import classes from './AgentListOption.module.scss';

interface Props {
  agent: Agent;
  onClick: (event: MouseEvent) => void;
}
export function AgentListOption({ agent, onClick }: Props) {
  const { display_name } = getAgentUiMetadata(agent);

  return (
    <li className={classes.root} onClick={onClick}>
      <div className={classes.content}>
        <div className={classes.name}>
          <span>{display_name}</span>

          <BeeBadge agent={agent} />
        </div>

        <AgentTags agent={agent} size="sm" />
      </div>
    </li>
  );
}

AgentListOption.Skeleton = function AgentListOptionSkeleton() {
  return (
    <li className={clsx(classes.root, classes.skeleton)}>
      <SkeletonText className={classes.name} width="50%" />
      <TagsList.Skeleton length={2} />
    </li>
  );
};

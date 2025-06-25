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

'use client';

import { spacing } from '@carbon/layout';
import { moderate01 } from '@carbon/motion';
import { ButtonSkeleton, SkeletonText } from '@carbon/react';
import clsx from 'clsx';
import { motion } from 'framer-motion';
import type { ReactNode } from 'react';

import { CopySnippet } from '#components/CopySnippet/CopySnippet.tsx';
import { MarkdownContent } from '#components/MarkdownContent/MarkdownContent.tsx';
import { TagsList } from '#components/TagsList/TagsList.tsx';
import commands from '#utils/commands.ts';
import { fadeProps } from '#utils/fadeProps.ts';

import type { Agent } from '../api/types';
import { AgentLaunchButton } from '../detail/AgentLaunchButton';
import { getAgentUiMetadata } from '../utils';
import classes from './AgentDetail.module.scss';
import { AgentDetailSection } from './AgentDetailSection';
import { AgentMetadata } from './AgentMetadata';
import { AgentTags } from './AgentTags';
import { BeeBadge } from './BeeBadge';

interface Props {
  agent: Agent;
  buttons?: ReactNode;
}

export function AgentDetail({ agent, buttons }: Props) {
  const {
    name,
    description,
    metadata: { documentation },
  } = agent;
  const { display_name } = getAgentUiMetadata(agent);

  return (
    <div className={classes.root}>
      <motion.header {...fadeInPropsWithMarginShift({ start: { from: spacing[4] } })} className={classes.header}>
        <h1 className={classes.name}>{display_name}</h1>

        <BeeBadge agent={agent} size="lg" />
      </motion.header>

      <motion.div {...fadeInPropsWithMarginShift({ start: { from: spacing[3] } })}>
        <AgentMetadata agent={agent} showSourceCodeLink className={classes.metadata} />

        {description && <MarkdownContent className={classes.description}>{description}</MarkdownContent>}

        <AgentTags agent={agent} className={classes.tags} />
      </motion.div>

      <motion.div
        {...fadeInPropsWithMarginShift({ start: { from: spacing[6], to: spacing[5] } })}
        className={classes.buttons}
      >
        <CopySnippet className={classes.copySnippet}>{commands.beeai.run(name)}</CopySnippet>

        {buttons}
      </motion.div>

      {documentation && (
        <motion.hr
          {...fadeInPropsWithMarginShift({
            start: { from: spacing[7], to: spacing[6] },
            end: { from: spacing[7], to: spacing[6] },
          })}
          className={classes.divider}
        />
      )}

      {documentation && (
        <motion.div {...fadeInPropsWithMarginShift()}>
          <AgentDetailSection title="Description" titleSpacing="large">
            <MarkdownContent className={classes.documentation}>{documentation}</MarkdownContent>
          </AgentDetailSection>
        </motion.div>
      )}
    </div>
  );
}

AgentDetail.Skeleton = function AgentDetailSkeleton() {
  return (
    <div className={classes.root}>
      <SkeletonText className={classes.name} width="50%" />

      <AgentMetadata.Skeleton className={classes.metadata} />

      <div className={classes.description}>
        <SkeletonText paragraph lineCount={3} />
      </div>

      <TagsList.Skeleton length={2} className={classes.tags} />

      <div className={classes.buttons}>
        <AgentLaunchButton.Skeleton />

        {/* .cds--layout--size-md fixes Carbon bug where button size prop is not respected */}
        <ButtonSkeleton size="md" className={clsx('cds--layout--size-md', classes.copySnippet)} />
      </div>

      <hr className={classes.divider} />

      <AgentDetailSection.Skeleton titleWidth="10rem" lineCount={6} />
    </div>
  );
};

function fadeInPropsWithMarginShift({
  start,
  end,
}: {
  start?: { from: string; to?: string };
  end?: { from: string; to?: string };
} = {}) {
  return fadeProps({
    hidden: {
      marginBlockStart: start ? start.from : undefined,
      marginBlockEnd: end ? end.from : undefined,
    },
    visible: {
      marginBlockStart: start ? start.to || 0 : undefined,
      marginBlockEnd: end ? end.to || 0 : undefined,
      transition: { delay: Number.parseFloat(moderate01) / 1000 },
    },
  });
}

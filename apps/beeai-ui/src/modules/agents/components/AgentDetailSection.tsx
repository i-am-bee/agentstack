/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { SkeletonText, type SkeletonTextProps } from '@carbon/react';
import clsx from 'clsx';
import type { ReactNode } from 'react';

import classes from './AgentDetailSection.module.scss';

interface Props {
  title: string;
  titleSpacing?: 'default' | 'large';
  children: ReactNode;
}

export function AgentDetailSection({ title, titleSpacing = 'default', children }: Props) {
  return (
    <section className={classes.section}>
      <h2 className={clsx(classes.title, classes[`${titleSpacing}Spacing`])}>{title}</h2>
      {children}
    </section>
  );
}

interface SkeletonProps {
  titleWidth: Required<SkeletonTextProps['width']>;
  lineCount: Required<SkeletonTextProps['lineCount']>;
}

AgentDetailSection.Skeleton = function AgentDetailSectionSkeleton({ titleWidth, lineCount }: SkeletonProps) {
  return (
    <>
      <SkeletonText className={clsx(classes.title, classes.defaultSpacing)} width={titleWidth} />
      <SkeletonText paragraph lineCount={lineCount} />
    </>
  );
};

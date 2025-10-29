/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { TagSkeleton } from '@carbon/react';
import clsx from 'clsx';
import type { ReactElement } from 'react';

import { SkeletonItems } from '#components/SkeletonItems/SkeletonItems.tsx';

import classes from './TagsList.module.scss';

interface Props {
  tags: ReactElement[];
  className?: string;
}

export function TagsList({ tags, className }: Props) {
  const hasTags = tags.length > 0;

  if (!hasTags) {
    return null;
  }

  return (
    <ul className={clsx(classes.root, className)}>
      {tags.map((tag, idx) => (
        <li key={idx}>{tag}</li>
      ))}
    </ul>
  );
}

interface SkeletonProps {
  length?: number;
  className?: string;
}

TagsList.Skeleton = function TagsListSkeleton({ length = 1, className }: SkeletonProps) {
  return (
    <div className={clsx(classes.root, className)}>
      <SkeletonItems count={length} render={(idx) => <TagSkeleton key={idx} />} />
    </div>
  );
};

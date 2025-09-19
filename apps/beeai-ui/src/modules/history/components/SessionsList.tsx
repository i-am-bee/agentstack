/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { SkeletonItems } from '#components/SkeletonItems/SkeletonItems.tsx';

import { SessionItem } from './SessionItem';
import classes from './SessionsList.module.scss';

interface Props {
  items?: SessionItem[];
  isLoading?: boolean;
}

export function SessionsList({ items = [], isLoading }: Props) {
  const noItems = items.length === 0 && !isLoading;

  if (noItems) {
    return (
      <>
        <p className={classes.empty}>
          <strong>No sessions yet</strong>
          <span>Start a conversation to see it here.</span>
        </p>
      </>
    );
  }

  return (
    <ul className={classes.root}>
      {isLoading ? (
        <SkeletonItems count={5} render={(idx) => <SessionItem.Skeleton key={idx} />} />
      ) : (
        items?.map(({ ...item }) => <SessionItem key={item.href} {...item} />)
      )}
    </ul>
  );
}

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { NoItemsMessage } from '#components/NoItemsMessage/NoItemsMessage.tsx';
import { SkeletonItems } from '#components/SkeletonItems/SkeletonItems.tsx';

import { SessionItem } from './SessionItem';
import classes from './SessionsList.module.scss';

interface Props {
  items: SessionItem[] | undefined;
  isLoading?: boolean;
}

export function SessionsList({ items = [], isLoading }: Props) {
  const noItems = items.length === 0 && !isLoading;

  if (noItems) {
    return <NoItemsMessage message="No session history" className={classes.empty} />;
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

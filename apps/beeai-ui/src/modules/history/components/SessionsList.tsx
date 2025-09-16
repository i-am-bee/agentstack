/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { SkeletonItems } from '#components/SkeletonItems/SkeletonItems.tsx';

import { SessionItem } from './SessionItem';
import classes from './SessionsList.module.scss';

interface Props {
  items?: SessionItem[];
}

export function SessionsList({ items }: Props) {
  return (
    <ul className={classes.root}>
      {items ? (
        items.map(({ ...item }) => <SessionItem key={item.href} {...item} />)
      ) : (
        <SkeletonItems count={5} render={(idx) => <SessionItem.Skeleton key={idx} />} />
      )}
    </ul>
  );
}

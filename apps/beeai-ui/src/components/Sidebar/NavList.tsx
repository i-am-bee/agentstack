/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { NoItemsMessage } from '#components/NoItemsMessage/NoItemsMessage.tsx';
import { SkeletonItems } from '#components/SkeletonItems/SkeletonItems.tsx';

import type { NavItemProps } from './NavItem';
import { NavItem } from './NavItem';
import classes from './NavList.module.scss';

interface Props {
  items: NavItemProps[] | undefined;
  isLoading?: boolean;
  skeletonCount?: number;
  noItemsMessage?: string;
}

export function NavList({ items = [], isLoading, skeletonCount = 10, noItemsMessage }: Props) {
  const noItems = items.length === 0 && !isLoading;

  if (noItems) {
    return noItemsMessage ? <NoItemsMessage message={noItemsMessage} className={classes.empty} /> : null;
  }

  return (
    <ul className={classes.root}>
      {isLoading ? (
        <SkeletonItems count={skeletonCount} render={(idx) => <NavItem.Skeleton key={idx} />} />
      ) : (
        items.map((item) => <NavItem key={item.href ?? item.label} {...item} />)
      )}
    </ul>
  );
}

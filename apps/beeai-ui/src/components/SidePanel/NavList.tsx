/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { SkeletonItems } from '#components/SkeletonItems/SkeletonItems.tsx';

import { NavItem } from './NavItem';
import classes from './NavList.module.scss';

type NavProps = {
  items?: NavItem[];
  skeletonCount?: number;
};

export function NavList({ items, skeletonCount = 10 }: NavProps) {
  return (
    <ul className={classes.root}>
      {items ? (
        items.map(({ key, ...item }) => <NavItem key={key} {...item} />)
      ) : (
        <SkeletonItems count={skeletonCount} render={(idx) => <NavItem.Skeleton key={idx} />} />
      )}
    </ul>
  );
}

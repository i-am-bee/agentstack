/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ArrowUpRight } from '@carbon/icons-react';
import { Button, ButtonSkeleton } from '@carbon/react';
import clsx from 'clsx';

import { SkeletonItems } from '#components/SkeletonItems/SkeletonItems.tsx';

import classes from './Nav.module.scss';

export type NavItem = {
  key: string;
  label: string;
  onClick: () => void;
  isActive?: boolean;
  isExternal?: boolean;
};

type NavProps = {
  title?: string;
  items?: NavItem[];
  skeletonCount?: number;
};

export function Nav({ title, items, skeletonCount = 10 }: NavProps) {
  return (
    <nav className={classes.root}>
      {title && <h2 className={classes.heading}>{title}</h2>}
      <ul className={classes.list}>{items ? renderItems(items) : renderSkeletons(skeletonCount)}</ul>
    </nav>
  );
}

function renderItems(items: NavItem[]) {
  return items.map(({ key, label, onClick, isActive, isExternal }) => (
    <li key={key}>
      <Button
        kind="ghost"
        size="sm"
        className={clsx(classes.button, { [classes.isActive]: isActive })}
        onClick={onClick}
      >
        {label}
        {isExternal && <ArrowUpRight className={classes.icon} />}
      </Button>
    </li>
  ));
}

function renderSkeletons(count: number) {
  return (
    <SkeletonItems
      count={count}
      render={(idx) => (
        <li key={idx}>
          <ButtonSkeleton size="sm" className={classes.button} />
        </li>
      )}
    />
  );
}

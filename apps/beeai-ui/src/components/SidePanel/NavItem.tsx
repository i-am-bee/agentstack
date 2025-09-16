/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ArrowUpRight } from '@carbon/icons-react';
import { Button, ButtonSkeleton } from '@carbon/react';
import clsx from 'clsx';

import classes from './NavItem.module.scss';

export interface NavItem {
  key: string;
  label: string;
  onClick: () => void;
  isActive?: boolean;
  isExternal?: boolean;
}

type Props = Omit<NavItem, 'key'>;

export function NavItem({ label, isActive, isExternal, onClick }: Props) {
  return (
    <li>
      <Button
        kind="ghost"
        size="sm"
        className={clsx(classes.button, { [classes.isActive]: isActive })}
        onClick={onClick}
      >
        {label}

        {isExternal && <ArrowUpRight />}
      </Button>
    </li>
  );
}

NavItem.Skeleton = function NavItemSkeleton() {
  return (
    <li>
      <ButtonSkeleton size="sm" className={classes.button} />
    </li>
  );
};

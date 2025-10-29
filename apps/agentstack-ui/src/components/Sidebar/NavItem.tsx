/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { CarbonIconType } from '@carbon/icons-react';
import { Button, ButtonSkeleton } from '@carbon/react';
import clsx from 'clsx';
import type { MouseEventHandler } from 'react';

import { TransitionLink } from '#components/TransitionLink/TransitionLink.tsx';

import classes from './NavItem.module.scss';

export interface NavItemProps {
  label: string;
  href?: string;
  Icon?: CarbonIconType;
  isActive?: boolean;
  isExternal?: boolean;
  hasDivider?: boolean;
  onClick?: MouseEventHandler<HTMLElement>;
}

export function NavItem({ label, href, Icon, isActive, isExternal }: NavItemProps) {
  return (
    <li>
      <Button
        href={href}
        kind="ghost"
        size="sm"
        className={clsx(classes.button, { [classes.isActive]: isActive })}
        {...(isExternal ? { target: '_blank', rel: 'noreferrer' } : { as: TransitionLink })}
      >
        {Icon && <Icon className={classes.icon} />}

        <span className={classes.label}>{label}</span>
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

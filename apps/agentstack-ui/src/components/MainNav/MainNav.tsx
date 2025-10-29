/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import type { CarbonIconType } from '@carbon/icons-react';
import { Button } from '@carbon/react';
import clsx from 'clsx';
import type { ReactNode } from 'react';

import { Tooltip } from '#components/Tooltip/Tooltip.tsx';
import { TransitionLink } from '#components/TransitionLink/TransitionLink.tsx';

import classes from './MainNav.module.scss';

interface Props {
  items: MainNavItem[];
}

export function MainNav({ items }: Props) {
  return (
    <nav>
      <ul className={classes.list}>
        {items.map((item) => (
          <MainNavItem key={item.href} item={item} />
        ))}
      </ul>
    </nav>
  );
}

export interface MainNavItem {
  label: ReactNode;
  href: string;
  Icon?: CarbonIconType;
  isExternal?: boolean;
  isActive?: boolean;
  disabled?: {
    tooltip: ReactNode;
  };
}

function MainNavItem({ item: { label, href, Icon, isExternal, isActive, disabled } }: { item: MainNavItem }) {
  const linkProps = { href, className: classes.link };
  const content = (
    <>
      {label}

      {Icon && <Icon />}
    </>
  );

  return (
    <li className={clsx({ [classes.active]: isActive })}>
      {disabled ? (
        <Tooltip asChild content={disabled.tooltip}>
          <Button kind="ghost" disabled className={classes.link}>
            {content}
          </Button>
        </Tooltip>
      ) : isExternal ? (
        <a {...linkProps} target="_blank" rel="noreferrer">
          {content}
        </a>
      ) : (
        <TransitionLink {...linkProps}>{content}</TransitionLink>
      )}
    </li>
  );
}

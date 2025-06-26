/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import type { CarbonIconType } from '@carbon/icons-react';
import { Button } from '@carbon/react';
import clsx from 'clsx';
import type { ComponentType, ReactNode } from 'react';

import { Tooltip } from '#components/Tooltip/Tooltip.tsx';

import classes from './MainNav.module.scss';

interface Props {
  items: MainNavItem[];
  linkComponent: ComponentType;
}

export function MainNav({ items, linkComponent }: Props) {
  return (
    <nav>
      <ul className={classes.list}>
        {items.map((item) => (
          <MainNavItem key={item.href} linkComponent={linkComponent} item={item} />
        ))}
      </ul>
    </nav>
  );
}

interface MainNavItem {
  label: ReactNode;
  href: string;
  Icon?: CarbonIconType;
  isExternal?: boolean;
  isActive?: boolean;
  disabled?: {
    tooltip: ReactNode;
  };
}

function MainNavItem({
  linkComponent,
  item: { label, href, Icon, isExternal, isActive, disabled },
}: {
  linkComponent: ComponentType;
  item: MainNavItem;
}) {
  const LinkComponent = isExternal ? 'a' : linkComponent;
  const linkProps = isExternal ? { target: '_blank', rel: 'noreferrer' } : null;

  return (
    <li className={clsx({ [classes.active]: isActive })}>
      {disabled ? (
        <Tooltip asChild content={disabled.tooltip}>
          <Button kind="ghost" disabled className={classes.link}>
            {label}

            {Icon && <Icon />}
          </Button>
        </Tooltip>
      ) : (
        <LinkComponent {...linkProps} href={href} className={classes.link}>
          {label}

          {Icon && <Icon />}
        </LinkComponent>
      )}
    </li>
  );
}

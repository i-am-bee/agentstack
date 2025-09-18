/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use client';

import type { CarbonIconType } from '@carbon/icons-react';
import { Launch, LogoGithub, Logout, Settings } from '@carbon/icons-react';
import { OverflowMenu, OverflowMenuItem } from '@carbon/react';
import clsx from 'clsx';
import { signOut } from 'next-auth/react';
import { useMemo } from 'react';

import UserAvatar from '#components/UserAvatar/UserAvatar.tsx';
import { useApp } from '#contexts/App/index.ts';
import { useRouteTransition } from '#contexts/TransitionContext/index.ts';
import { useBreakpointUp } from '#hooks/useBreakpoint.ts';
import { DOCUMENTATION_LINK, GET_SUPPORT_LINK } from '#utils/constants.ts';
import { routes } from '#utils/router.ts';

import classes from './UserNav.module.scss';

export function UserNav() {
  const { transitionTo } = useRouteTransition();
  const { setNavigationOpen, isAuthEnabled } = useApp();
  const isMaxUp = useBreakpointUp('max');

  const items: NavItem[] = useMemo(
    () =>
      isAuthEnabled
        ? [
            ...NAV_ITEMS,
            {
              itemText: 'Log out',
              icon: Logout,
              hasDivider: true,
              onClick: () => {
                signOut({ redirectTo: routes.signIn() });
              },
            },
          ]
        : NAV_ITEMS,
    [isAuthEnabled],
  );

  return (
    <OverflowMenu
      renderIcon={isAuthEnabled ? UserAvatar : Settings}
      size="sm"
      aria-label="User navigation"
      direction="top"
      className={clsx(classes.button, { [classes.avatar]: isAuthEnabled })}
      menuOptionsClass={classes.menu}
    >
      {items.map(({ hasDivider, itemText, icon: Icon, isInternal, href, onClick, ...props }, idx) => {
        return (
          <OverflowMenuItem
            key={idx}
            {...props}
            href={href}
            target={!isInternal ? '_blank' : undefined}
            onClick={(event) => {
              onClick?.(event);

              if (isInternal && href) {
                transitionTo(href);

                if (!isMaxUp) {
                  setNavigationOpen(false);
                }

                event.preventDefault();
              }
            }}
            itemText={
              Icon ? (
                <>
                  <span className="cds--overflow-menu-options__option-content">{itemText}</span> <Icon />
                </>
              ) : (
                itemText
              )
            }
            hasDivider={hasDivider}
          />
        );
      })}
    </OverflowMenu>
  );
}

interface NavItem {
  itemText: string;
  href?: string;
  isInternal?: boolean;
  icon?: React.ComponentType<React.ComponentProps<'svg'>> | CarbonIconType;
  hasDivider?: boolean;
  onClick?: (event: React.MouseEvent<HTMLElement, MouseEvent>) => void;
}

const NAV_ITEMS: NavItem[] = [
  {
    itemText: 'App settings',
    href: routes.settings(),
    isInternal: true,
  },
  {
    itemText: 'Documentation',
    href: DOCUMENTATION_LINK,
    icon: Launch,
    hasDivider: true,
  },
  {
    itemText: 'Get support',
    href: GET_SUPPORT_LINK,
    icon: LogoGithub,
  },
];

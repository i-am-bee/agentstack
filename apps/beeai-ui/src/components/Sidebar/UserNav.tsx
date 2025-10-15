/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { LogoGithub, Logout, Settings } from '@carbon/icons-react';
import { OverflowMenu, OverflowMenuItem } from '@carbon/react';
import { signOut } from 'next-auth/react';
import type { PropsWithChildren } from 'react';
import { useMemo } from 'react';

import UserAvatar from '#components/UserAvatar/UserAvatar.tsx';
import { useApp } from '#contexts/App/index.ts';
import { useRouteTransition } from '#contexts/TransitionContext/index.ts';
import { useBreakpointUp } from '#hooks/useBreakpoint.ts';
import { GET_SUPPORT_LINK } from '#utils/constants.ts';
import { routes } from '#utils/router.ts';

import type { NavItemProps } from './NavItem';
import classes from './UserNav.module.scss';

export function UserNav() {
  const { transitionTo } = useRouteTransition();
  const {
    setSidebarOpen,
    config: { isAuthEnabled },
  } = useApp();
  const isMaxUp = useBreakpointUp('max');

  const items: NavItemProps[] = useMemo(
    () =>
      isAuthEnabled
        ? [
            ...NAV_ITEMS,
            {
              label: 'Log out',
              Icon: Logout,
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
      className={classes.button}
      menuOptionsClass={classes.menu}
    >
      {items.map(({ label, href, Icon, isExternal, hasDivider, onClick }, idx) => {
        return (
          <OverflowMenuItem
            key={idx}
            href={href}
            onClick={(event) => {
              onClick?.(event);

              if (isExternal) {
                return;
              }

              if (href) {
                transitionTo(href);

                if (!isMaxUp) {
                  setSidebarOpen(false);
                }

                event.preventDefault();
              }
            }}
            itemText={<Label Icon={Icon}>{label}</Label>}
            hasDivider={hasDivider}
            {...(isExternal ? { target: '_blank', rel: 'noreferrer' } : {})}
          />
        );
      })}
    </OverflowMenu>
  );
}

const NAV_ITEMS: NavItemProps[] = [
  {
    label: 'App settings',
    href: routes.settings(),
  },
  {
    label: 'Get support',
    href: GET_SUPPORT_LINK,
    Icon: LogoGithub,
    isExternal: true,
    hasDivider: true,
  },
];

function Label({ Icon, children }: PropsWithChildren<Pick<NavItemProps, 'Icon'>>) {
  if (Icon) {
    return (
      <>
        <span className="cds--overflow-menu-options__option-content">{children}</span> <Icon />
      </>
    );
  }

  return children;
}

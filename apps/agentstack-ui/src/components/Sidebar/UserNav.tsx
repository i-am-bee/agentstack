/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { Logout } from '@carbon/icons-react';
import { OverflowMenu, OverflowMenuItem } from '@carbon/react';
import { signOut } from 'next-auth/react';
import type { PropsWithChildren } from 'react';
import { useMemo } from 'react';

import UserAvatar from '#components/UserAvatar/UserAvatar.tsx';
import { useRouteTransition } from '#contexts/TransitionContext/index.ts';
import { routes } from '#utils/router.ts';

import type { NavItemProps } from './NavItem';
import classes from './UserNav.module.scss';

export function UserNav() {
  const { transitionTo } = useRouteTransition();

  const items: NavItemProps[] = useMemo(
    () => [
      {
        label: 'Log out',
        Icon: Logout,
        onClick: () => signOut({ redirectTo: routes.signIn() }),
      },
    ],
    [],
  );

  return (
    <div className={classes.root}>
      <OverflowMenu
        renderIcon={UserAvatar}
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
    </div>
  );
}

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

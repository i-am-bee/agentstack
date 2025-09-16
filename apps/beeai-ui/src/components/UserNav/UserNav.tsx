/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Launch, LogoGithub, Settings } from '@carbon/icons-react';
import { OverflowMenu, OverflowMenuItem } from '@carbon/react';
import clsx from 'clsx';

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

  return (
    <OverflowMenu
      renderIcon={isAuthEnabled ? UserAvatar : Settings}
      size="sm"
      aria-label="User navigation"
      direction="top"
      className={clsx(classes.button, { [classes.avatar]: isAuthEnabled })}
      menuOptionsClass={classes.menu}
    >
      {NAV_ITEMS.map(({ hasDivider, itemText, icon: Icon, isInternal, href, ...props }, idx) => {
        return (
          <OverflowMenuItem
            key={idx}
            {...props}
            href={href}
            target={!isInternal ? '_blank' : undefined}
            onClick={(event) => {
              if (isInternal) {
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

const NAV_ITEMS = [
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

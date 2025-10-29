/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { HeaderMenuItem, HeaderSideNavItems, SideNav, SideNavItems } from '@carbon/react';
import type { MainNavItem } from '@i-am-bee/agentstack-ui';

import classes from './MobileSideNav.module.scss';

interface Props {
  items: MainNavItem[];
  isExpanded: boolean;
}

export function MobileSideNav({ items, isExpanded }: Props) {
  return (
    <SideNav isPersistent={false} expanded={isExpanded}>
      <SideNavItems>
        <HeaderSideNavItems>
          {items.map(({ label, href, Icon }, idx) => (
            <HeaderMenuItem href={href} target="_blank" key={idx}>
              <span className={classes.itemContent}>
                {label}
                {Icon && <Icon />}
              </span>
            </HeaderMenuItem>
          ))}
        </HeaderSideNavItems>
      </SideNavItems>
    </SideNav>
  );
}

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use client';
import { ArrowUpRight } from '@carbon/icons-react';
import { HeaderMenuButton } from '@carbon/react';
import { MainNav } from '@i-am-bee/agentstack-ui';
import clsx from 'clsx';
import Link from 'next/link';
import { useState } from 'react';

import { AGENT_STACK_DOCS_LINK, APP_NAME, FRAMEWORK_DOCS_LINK } from '@/constants';
import { routeDefinitions } from '@/utils/router';

import classes from './AppHeader.module.scss';
import { LayoutContainer } from './LayoutContainer';
import { MobileSideNav } from './MobileSideNav';
import { SocialLinks } from './SocialLinks';

interface Props {
  className?: string;
}

export function AppHeader({ className }: Props) {
  const [isSideNavExpanded, setSideNavExpanded] = useState(false);

  return (
    <header className={clsx(classes.root, className)}>
      <LayoutContainer asGrid>
        <div className={classes.content}>
          <nav className={classes.nav}>
            <HeaderMenuButton
              aria-label="Open menu"
              onClick={() => setSideNavExpanded((expanded) => !expanded)}
              isActive={isSideNavExpanded}
              className={classes.toggleMenuBtn}
            />

            <Link href={routeDefinitions.home} className={classes.logo}>
              <strong>{APP_NAME}</strong>
            </Link>

            <div className={classes.navItems}>
              <MainNav items={items} />
            </div>

            <MobileSideNav items={items} isExpanded={isSideNavExpanded} />
          </nav>

          <div className={classes.right}>
            <SocialLinks />
          </div>
        </div>
      </LayoutContainer>
    </header>
  );
}

const items = [
  {
    label: 'BeeAI Framework Docs',
    href: FRAMEWORK_DOCS_LINK,
    Icon: ArrowUpRight,
    isExternal: true,
  },
  {
    label: 'Agent Stack Docs',
    href: AGENT_STACK_DOCS_LINK,
    Icon: ArrowUpRight,
    isExternal: true,
  },
  {
    label: 'Blog',
    href: routeDefinitions.blog,
  },
];

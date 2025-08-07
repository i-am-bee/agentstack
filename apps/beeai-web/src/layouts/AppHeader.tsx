/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use client';
import { ArrowUpRight } from '@carbon/icons-react';
import { HeaderMenuButton, HeaderMenuItem, HeaderSideNavItems, SideNav, SideNavItems } from '@carbon/react';
import { DOCUMENTATION_LINK, MainNav } from '@i-am-bee/beeai-ui';
import clsx from 'clsx';
import Link from 'next/link';
import { useState } from 'react';

import { FRAMEWORK_DOCS_LINK } from '@/constants';

import classes from './AppHeader.module.scss';
import { LayoutContainer } from './LayoutContainer';
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

            <Link href="/" className={classes.logo}>
              <strong>BeeAI</strong>
            </Link>

            <div className={classes.navItems}>
              <MainNav items={items} />
            </div>

            <SideNav isPersistent={false} expanded={isSideNavExpanded}>
              <SideNavItems>
                <HeaderSideNavItems>
                  {items.map(({ label, href }, idx) => (
                    <HeaderMenuItem href={href} target="_blank" key={idx}>
                      {label}
                    </HeaderMenuItem>
                  ))}
                </HeaderSideNavItems>
              </SideNavItems>
            </SideNav>
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
    label: 'Framework Docs',
    href: FRAMEWORK_DOCS_LINK,
    Icon: ArrowUpRight,
    isExternal: true,
  },
  {
    label: 'Platform Docs',
    href: DOCUMENTATION_LINK,
    Icon: ArrowUpRight,
    isExternal: true,
  },
];

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use client';

import { ArrowUpRight } from '@carbon/icons-react';
import { DOCUMENTATION_LINK, MainNav } from '@i-am-bee/beeai-ui';
import clsx from 'clsx';
import Link from 'next/link';

import { FRAMEWORK_DOCS_LINK } from '@/constants';

import classes from './AppHeader.module.scss';
import { LayoutContainer } from './LayoutContainer';
import { SocialLinks } from './SocialLinks';

interface Props {
  className?: string;
}

export function AppHeader({ className }: Props) {
  return (
    <header className={clsx(classes.root, className)}>
      <LayoutContainer asGrid>
        <nav className={classes.nav}>
          <Link href="/" className={classes.logo}>
            <strong>BeeAI</strong>
          </Link>

          <div className={classes.navItems}>
            <MainNav items={items} />
          </div>
        </nav>

        <div className={classes.right}>
          <SocialLinks />
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

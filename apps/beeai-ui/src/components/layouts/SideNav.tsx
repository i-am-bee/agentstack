/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { usePathname } from 'next/navigation';
import { type RefObject, useEffect, useRef } from 'react';
import { useOnClickOutside } from 'usehooks-ts';

import { AgentsNav } from '#components/AgentsNav/AgentsNav.tsx';
import { SidebarButton } from '#components/AppHeader/SidebarButton.tsx';
import { CustomNav } from '#components/CustomNav/CustomNav.tsx';
import { SidePanel } from '#components/SidePanel/SidePanel.tsx';
import { UserNav } from '#components/UserNav/UserNav.tsx';
import { useApp } from '#contexts/App/index.ts';
import { NAV_ITEMS } from '#utils/constants.ts';

import classes from './SideNav.module.scss';

type NavVariant = 'custom' | 'agents';

export function SideNav() {
  const pathname = usePathname();
  const { navigationOpen, closeNavOnClickOutside, setNavigationOpen } = useApp();
  const navRef = useRef<HTMLDivElement>(null);
  const navVariant: NavVariant = NAV_ITEMS.length ? 'custom' : 'agents';

  useOnClickOutside(navRef as RefObject<HTMLDivElement>, () => {
    if (closeNavOnClickOutside || navVariant === 'custom') {
      setNavigationOpen(false);
    }
  });

  useEffect(() => {
    if (navVariant === 'custom') {
      setNavigationOpen(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [setNavigationOpen, pathname]);

  return (
    <div ref={navRef}>
      <SidebarButton />

      <SidePanel variant="left" isOpen={navigationOpen}>
        <div className={classes.root}>
          {navVariant === 'custom' && <CustomNav items={NAV_ITEMS} />}
          {navVariant === 'agents' && <AgentsNav />}

          <div className={classes.footer}>
            <UserNav />
          </div>
        </div>
      </SidePanel>
    </div>
  );
}

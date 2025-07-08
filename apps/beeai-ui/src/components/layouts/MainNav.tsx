/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { type RefObject, useRef } from 'react';
import { useOnClickOutside } from 'usehooks-ts';

import { AgentsNav } from '#components/AgentsNav/AgentsNav.tsx';
import { SidebarButton } from '#components/AppHeader/SidebarButton.tsx';
import { SidePanel } from '#components/SidePanel/SidePanel.tsx';
import { UserNav } from '#components/UserNav/UserNav.tsx';
import { useApp } from '#contexts/App/index.ts';
import { useAppConfig } from '#contexts/AppConfig/index.ts';

import classes from './MainNav.module.scss';

export function MainNav() {
  const { navigationOpen, closeNavOnClickOutside, setNavigationOpen } = useApp();
  const { featureFlags } = useAppConfig();
  const navRef = useRef<HTMLDivElement>(null);

  useOnClickOutside(navRef as RefObject<HTMLDivElement>, () => {
    if (closeNavOnClickOutside) {
      setNavigationOpen(false);
    }
  });

  return (
    <div ref={navRef}>
      <SidebarButton />

      <SidePanel variant="left" isOpen={navigationOpen}>
        <div className={classes.root}>
          <AgentsNav />

          {featureFlags?.user_navigation && (
            <div className={classes.footer}>
              <UserNav />
            </div>
          )}
        </div>
      </SidePanel>
    </div>
  );
}

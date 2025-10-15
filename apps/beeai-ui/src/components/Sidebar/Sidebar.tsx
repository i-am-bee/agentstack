/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import clsx from 'clsx';
import { useRef } from 'react';
import { useOnClickOutside } from 'usehooks-ts';

import { useApp } from '#contexts/App/index.ts';
import { SessionsNav } from '#modules/history/components/SessionsNav.tsx';

import { AgentsNav } from './AgentsNav';
import { MainNav } from './MainNav';
import classes from './Sidebar.module.scss';
import { SidebarButton } from './SidebarButton';
import { SideNav } from './SideNav';
import { UserNav } from './UserNav';

interface Props {
  className?: string;
}

export function Sidebar({ className }: Props) {
  const navRef = useRef<HTMLDivElement>(null);

  const { sidebarOpen, closeSidebarOnClickOutside, setSidebarOpen } = useApp();

  useOnClickOutside(navRef, () => {
    if (closeSidebarOnClickOutside) {
      setSidebarOpen(false);
    }
  });

  return (
    <div ref={navRef} className={clsx(classes.root, className, { [classes.isOpen]: sidebarOpen })}>
      <div className={classes.content}>
        <header className={classes.stack}>
          <SidebarButton />

          <MainNav />
        </header>

        <div className={classes.body}>
          <div className={classes.bodyContent}>
            <AgentsNav className={classes.agentsNav} />

            <SessionsNav />
          </div>
        </div>

        <footer className={classes.stack}>
          <SideNav />

          <UserNav />
        </footer>
      </div>
    </div>
  );
}

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import clsx from 'clsx';
import type { PropsWithChildren } from 'react';

import { Sidebar } from '#components/Sidebar/Sidebar.tsx';
import { useApp } from '#contexts/App/index.ts';

import classes from './AppLayout.module.scss';

export function AppLayout({ children }: PropsWithChildren) {
  const { sidebarOpen } = useApp();

  return (
    <div className={clsx(classes.root, { ['sidebar-open']: sidebarOpen })}>
      <Sidebar className={classes.sidebar} />

      <main className={classes.main} data-route-transition>
        {children}
      </main>
    </div>
  );
}

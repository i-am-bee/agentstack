/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { PropsWithChildren } from 'react';

import { Sidebar } from '#components/Sidebar/Sidebar.tsx';

import classes from './AppLayout.module.scss';

export function AppLayout({ children }: PropsWithChildren) {
  return (
    <div className={classes.root}>
      <Sidebar className={classes.sidebar} />

      <main className={classes.main} data-route-transition>
        {children}
      </main>
    </div>
  );
}

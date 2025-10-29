/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { PropsWithChildren } from 'react';

import { AppHeader } from './AppHeader';
import classes from './AppLayout.module.scss';

export default function AppLayout({ children }: PropsWithChildren) {
  return (
    <div className={classes.root}>
      <AppHeader className={classes.header} />

      <main className={classes.main} data-route-transition>
        {children}
      </main>
    </div>
  );
}

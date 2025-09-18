/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { type PropsWithChildren, Suspense } from 'react';

import { AppHeader } from '#components/AppHeader/AppHeader.tsx';

import classes from './AppLayout.module.scss';

export function AppLayout({ children }: PropsWithChildren) {
  return (
    <div className={classes.root}>
      <Suspense>
        <AppHeader className={classes.header} />
      </Suspense>

      <main className={classes.main} data-route-transition>
        {children}
      </main>
    </div>
  );
}

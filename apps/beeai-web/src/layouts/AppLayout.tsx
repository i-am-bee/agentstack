/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { GitHubLink } from '@i-am-bee/beeai-ui';
import type { PropsWithChildren } from 'react';

import { AppHeader } from './AppHeader';
import classes from './AppLayout.module.scss';
import { Navigation } from './Navigation';

export default function AppLayout({ children }: PropsWithChildren) {
  return (
    <div className={classes.root}>
      <AppHeader className={classes.header}>
        <Navigation />

        <GitHubLink />
      </AppHeader>

      <main className={classes.main} data-route-transition>
        {children}
      </main>
    </div>
  );
}

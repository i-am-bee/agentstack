/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { PropsWithChildren } from 'react';

import { AppHeader } from '#components/AppHeader/AppHeader.tsx';
import { AgentDetailPanel } from '#modules/agents/components/AgentDetailPanel.tsx';

import classes from './AppLayout.module.scss';

export function AppLayout({ children }: PropsWithChildren) {
  return (
    <div className={classes.root}>
      <AppHeader className={classes.header} />

      <main className={classes.main} data-transition>
        {children}

        <AgentDetailPanel />
      </main>
    </div>
  );
}

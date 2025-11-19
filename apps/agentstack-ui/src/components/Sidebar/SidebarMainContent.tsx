/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';

import { SessionsNav } from '#modules/history/components/SessionsNav.tsx';

import { AgentsNav } from './AgentsNav';
import classes from './SidebarMainContent.module.scss';

interface Props {
  className?: string;
}

export function SidebarMainContent({ className }: Props) {
  return (
    <div className={clsx(classes.root, className)}>
      <AgentsNav className={classes.agentsNav} />

      <SessionsNav className={classes.sessions} />
    </div>
  );
}

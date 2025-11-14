/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';

import { useParamsFromUrl } from '#hooks/useParamsFromUrl.ts';
import { SessionsNav } from '#modules/history/components/SessionsNav.tsx';

import { AgentNav } from './AgentNav';
import { AgentsNav } from './AgentsNav';
import { RecentlyUsedAgentsNav } from './RecentlyUsedAgentsNav';
import classes from './SidebarMainContent.module.scss';

interface Props {
  className?: string;
}

export function SidebarMainContent({ className }: Props) {
  const { providerId } = useParamsFromUrl();

  return (
    <div className={clsx(classes.root, className)}>
      {providerId ? (
        <>
          <AgentNav providerId={providerId} />

          <SessionsNav providerId={providerId} className={classes.sessions} />
        </>
      ) : (
        <>
          <AgentsNav className={classes.agentsNav} />

          <RecentlyUsedAgentsNav className={classes.recentlyUsed} />
        </>
      )}
    </div>
  );
}

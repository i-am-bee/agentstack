/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';
import clsx from 'clsx';
import type { TransitionEvent, TransitionEventHandler } from 'react';
import { useCallback, useRef, useState } from 'react';

import { useApp } from '#contexts/App/index.ts';

// import { useParamsFromUrl } from '#hooks/useParamsFromUrl.ts';
// import { useAgent } from '#modules/agents/api/queries/useAgent.ts';
// import { SessionsNav } from '#modules/history/components/SessionsNav.tsx';
// import { AgentNav } from './AgentNav';
import { AgentsNav } from './AgentsNav';
import { MainNav } from './MainNav';
import { RecentlyUsedAgentsNav } from './RecentlyUsedAgentsNav';
import classes from './Sidebar.module.scss';
import { SidebarButton } from './SidebarButton';
import { SideNav } from './SideNav';
import { UserNav } from './UserNav';

interface Props {
  className?: string;
}

export function Sidebar({ className }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const [isAnimating, setIsAnimating] = useState(false);

  // const { providerId } = useParamsFromUrl();
  // const { data: agent } = useAgent({ providerId });

  const {
    config: { isAuthEnabled },
    sidebarOpen,
  } = useApp();

  const checkTransition = useCallback((event: TransitionEvent) => {
    const {
      target,
      currentTarget,
      nativeEvent: { propertyName },
    } = event;

    return target === currentTarget && propertyName === 'width';
  }, []);

  const handleTransitionStart: TransitionEventHandler = useCallback(
    (event) => {
      if (checkTransition(event)) {
        setIsAnimating(true);
      }
    },
    [checkTransition],
  );

  const handleTransitionEnd: TransitionEventHandler = useCallback(
    (event) => {
      if (checkTransition(event)) {
        setIsAnimating(false);
      }
    },
    [checkTransition],
  );

  return (
    <div
      ref={ref}
      className={clsx(classes.root, className, {
        [classes.isOpen]: sidebarOpen,
        [classes.isAnimating]: isAnimating,
      })}
      onTransitionStart={handleTransitionStart}
      onTransitionEnd={handleTransitionEnd}
    >
      <div className={classes.content}>
        <header className={classes.stack}>
          <SidebarButton />

          <MainNav />
        </header>

        <div className={classes.body}>
          <div className={classes.bodyContent}>
            <AgentsNav className={classes.agentsNav} />

            <RecentlyUsedAgentsNav className={classes.recentlyUsed} />

            {/* {agent && <AgentNav agent={agent} />} */}

            {/* <SessionsNav /> */}
          </div>
        </div>

        <footer className={classes.stack}>
          <SideNav />

          {isAuthEnabled && (
            <>
              <hr className={classes.separator} />

              <UserNav />
            </>
          )}
        </footer>
      </div>
    </div>
  );
}

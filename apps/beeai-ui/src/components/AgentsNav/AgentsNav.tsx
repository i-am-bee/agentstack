/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button, ButtonSkeleton } from '@carbon/react';
import clsx from 'clsx';
import { useLocation } from 'react-router';

import { SkeletonItems } from '#components/SkeletonItems/SkeletonItems.tsx';
import { useViewTransition } from '#hooks/useViewTransition.ts';
import { useListAgents } from '#modules/agents/api/queries/useListAgents.ts';
import { getAgentDisplayName } from '#modules/agents/utils.ts';
import { routes } from '#utils/router.ts';

import classes from './AgentsNav.module.scss';

export function AgentsNav() {
  const { pathname } = useLocation();
  const { transitionTo } = useViewTransition();

  const { data: agents, isPending } = useListAgents({ onlyUiSupported: true, sort: true });

  return (
    <nav className={classes.root}>
      <h2 className={classes.heading}>Agents</h2>

      <ul className={classes.list}>
        {!isPending ? (
          agents?.map((agent) => {
            const { name } = agent;
            const route = routes.agentRun({ name });
            const isActive = pathname === route;

            return (
              <li key={name}>
                <Button
                  kind="ghost"
                  size="sm"
                  className={clsx(classes.button, { [classes.isActive]: isActive })}
                  onClick={() => transitionTo(route)}
                >
                  {getAgentDisplayName(agent)}
                </Button>
              </li>
            );
          })
        ) : (
          <SkeletonItems
            count={10}
            render={(idx) => (
              <li key={idx}>
                <ButtonSkeleton size="sm" className={classes.button} />
              </li>
            )}
          />
        )}
      </ul>
    </nav>
  );
}

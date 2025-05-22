/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { Button, ButtonSkeleton } from '@carbon/react';
import clsx from 'clsx';
import { useLocation } from 'react-router';

import { SkeletonItems } from '#components/SkeletonItems/SkeletonItems.tsx';
import { useViewTransition } from '#hooks/useViewTransition.ts';
import { useListAgents } from '#modules/agents/api/queries/useListAgents.ts';
import { getAgentDisplayName, isAgentUiSupported, sortAgentsByName } from '#modules/agents/utils.ts';
import { routes } from '#utils/router.ts';

import classes from './AgentsNav.module.scss';

export function AgentsNav() {
  const { pathname } = useLocation();
  const { transitionTo } = useViewTransition();

  const { data, isPending } = useListAgents();
  const agents = data?.filter(isAgentUiSupported).sort(sortAgentsByName);

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

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

import { Loading } from '@carbon/react';
import { useEffect } from 'react';

import { useViewTransition } from '#hooks/useViewTransition.ts';
import { useListAgents } from '#modules/agents/api/queries/useListAgents.ts';
import { sortAgentsByName } from '#modules/agents/utils.ts';
import { routes } from '#utils/router.ts';

import classes from './Landing.module.scss';

export function Landing() {
  const { data } = useListAgents();
  const { transitionTo } = useViewTransition();

  const agents = data?.sort(sortAgentsByName);

  useEffect(() => {
    const firstAgent = agents?.at(0);
    if (firstAgent) {
      transitionTo(routes.agentRun({ name: firstAgent.name }));
    }
  }, [agents, transitionTo]);

  return (
    <div className={classes.root}>
      <Loading withOverlay={false} />
    </div>
  );
}

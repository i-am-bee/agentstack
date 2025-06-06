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

import clsx from 'clsx';
import { useParams } from 'react-router';

import { MainNav } from '#components/layouts/MainNav.tsx';
import { useAgent } from '#modules/agents/api/queries/useAgent.ts';
import type { AgentPageParams } from '#modules/agents/types.ts';
import { getAgentDisplayName } from '#modules/agents/utils.ts';
import { NAV } from '#utils/vite-constants.ts';

import { Container } from '../layouts/Container';
import { AgentDetailButton } from './AgentDetailButton';
import classes from './AppHeader.module.scss';
import { AppHeaderNav } from './AppHeaderNav';

interface Props {
  className?: string;
}

export function AppHeader({ className }: Props) {
  const { agentName } = useParams<AgentPageParams>();
  const { data: agent } = useAgent({ name: agentName ?? '' });

  return (
    <header className={clsx(classes.root, className)}>
      <Container size="full">
        <div className={clsx(classes.holder, { [classes.hasNav]: NAV.length > 0 })}>
          <MainNav />

          {NAV.length > 0 && <AppHeaderNav items={NAV} />}
          {!NAV.length && agent && (
            <>
              <p className={classes.agentName}>{getAgentDisplayName(agent)}</p>
              <AgentDetailButton />
            </>
          )}
        </div>
      </Container>
    </header>
  );
}

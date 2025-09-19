/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';
import clsx from 'clsx';

import { SideNav } from '#components/layouts/SideNav.tsx';
import { useParamsFromUrl } from '#hooks/useParamsFromUrl.ts';
import { useAgent } from '#modules/agents/api/queries/useAgent.ts';
import { NAV_ITEMS } from '#utils/constants.ts';
import { isNotNull } from '#utils/helpers.ts';

import { Container } from '../layouts/Container';
import { AgentDetailButton } from './AgentDetailButton';
import classes from './AppHeader.module.scss';
import { AppHeaderNav } from './AppHeaderNav';

interface Props {
  className?: string;
}

export function AppHeader({ className }: Props) {
  const { providerId } = useParamsFromUrl();

  const { data: agent } = useAgent({ providerId });
  const hasNav = NAV_ITEMS.length > 0;
  const showAgent = !hasNav && isNotNull(agent);
  return (
    <header className={clsx(classes.root, className)}>
      <Container size="full">
        <div className={clsx(classes.holder, { [classes.hasNav]: hasNav })}>
          <SideNav />

          {hasNav && <AppHeaderNav items={NAV_ITEMS} />}

          {showAgent && (
            <>
              <p className={classes.agentName}>{agent.name}</p>

              <div className={classes.agentDetailButtonContainer}>
                <AgentDetailButton />
              </div>
            </>
          )}
        </div>
      </Container>
    </header>
  );
}

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Container } from '#components/layouts/Container.tsx';
import { MainContent } from '#components/layouts/MainContent.tsx';
import { fetchProviders } from '#modules/providers/api/index.ts';
import { DOCUMENTATION_LINK } from '#utils/constants.ts';

import { USER_NOT_OWNED_AGENTS_LIST_PARAMS, USER_OWNED_AGENTS_LIST_PARAMS } from '../constants';
import { DiscoverAgentsList } from './DiscoverAgentsList';
import { HomeHeading } from './HomeHeading';
import classes from './HomeView.module.scss';
import { RecentlyAddedAgentsList } from './RecentlyAddedAgentsList';
import { RecentlyUsedAgentsList } from './RecentlyUsedAgentsList';

export async function HomeView() {
  const [userOwned, userNotOwned] = await Promise.all([
    fetchProviders(USER_OWNED_AGENTS_LIST_PARAMS),
    fetchProviders(USER_NOT_OWNED_AGENTS_LIST_PARAMS),
  ]);

  const hasUserOwnedAgents = userOwned && userOwned.total_count > 0;

  return (
    <MainContent spacing="sm">
      <Container className={classes.root}>
        {!hasUserOwnedAgents && <HomeHeading />}

        <RecentlyAddedAgentsList initialData={userOwned} />

        <RecentlyUsedAgentsList initialData={userNotOwned} />

        <DiscoverAgentsList initialData={userNotOwned} />

        <footer className={classes.footer}>
          <p className={classes.infoText}>
            Want to build an agent but not sure where to start? Check out our{' '}
            <a href={DOCUMENTATION_LINK} target="_blank" rel="noreferrer">
              documentation
            </a>
            .
          </p>
        </footer>
      </Container>
    </MainContent>
  );
}

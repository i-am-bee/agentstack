/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Container } from '#components/layouts/Container.tsx';
import { MainContent } from '#components/layouts/MainContent.tsx';
import { fetchProviders } from '#modules/providers/api/index.ts';

import { DiscoverAgentsList } from './DiscoverAgentsList';
import { HomeHeading } from './HomeHeading';
import classes from './HomeView.module.scss';

export async function HomeView() {
  const initialData = await fetchProviders();

  return (
    <MainContent spacing="sm">
      <Container className={classes.root}>
        <HomeHeading />

        <DiscoverAgentsList initialData={initialData} />
      </Container>
    </MainContent>
  );
}

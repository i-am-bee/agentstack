/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Container } from '#components/layouts/Container.tsx';
import { MainContent } from '#components/layouts/MainContent.tsx';
import { AgentCardsList } from '#modules/agents/components/cards/AgentCardsList.tsx';
import { DOCUMENTATION_LINK } from '#utils/constants.ts';

import { HomeHeading } from './HomeHeading';
import classes from './HomeView.module.scss';

export function HomeView() {
  return (
    <MainContent spacing="sm">
      <Container className={classes.root}>
        <HomeHeading />

        <AgentCardsList heading="Discover agents" description="See working agents in action and try them instantly." />

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

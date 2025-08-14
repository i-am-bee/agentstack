/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Container } from '#components/layouts/Container.tsx';
import { MainContent } from '#components/layouts/MainContent.tsx';
import type { Agent } from '#modules/agents/api/types.ts';
import { AgentHeading } from '#modules/agents/components/AgentHeading.tsx';

import classes from './UiNotAvailableView.module.scss';

interface Props {
  agent: Agent;
}

export function UiNotAvailableView({ agent }: Props) {
  const { interaction_mode } = agent.ui;

  return (
    <MainContent>
      <Container size="sm" className={classes.root}>
        <AgentHeading agent={agent} />

        <p className={classes.description}>
          {interaction_mode
            ? `The UI type requested by the agent is not available: '${interaction_mode}'`
            : 'The agent doesn’t have a defined UI type.'}
        </p>
      </Container>
    </MainContent>
  );
}

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Container } from '#components/layouts/Container.tsx';
import { AgentGreeting } from '#modules/agents/components/AgentGreeting.tsx';
import { AgentHeading } from '#modules/agents/components/AgentHeading.tsx';

import { useAgentRun } from '../contexts/agent-run';
import { FileUpload } from '../files/components/FileUpload';
import { HandsOffInput } from './HandsOffInput';
import classes from './HandsOffLandingView.module.scss';

export function HandsOffLandingView() {
  const { agent } = useAgentRun();

  return (
    <FileUpload>
      <Container size="sm" className={classes.root}>
        <div className={classes.header}>
          <AgentHeading agent={agent} />

          <AgentGreeting agent={agent} />
        </div>

        <HandsOffInput />
      </Container>
    </FileUpload>
  );
}

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Container } from '#components/layouts/Container.tsx';
import { AgentGreeting } from '#modules/agents/components/AgentGreeting.tsx';
import { AgentHeading } from '#modules/agents/components/AgentHeading.tsx';

import { useAgentRun } from '../contexts/agent-run';
import { FileUpload } from '../files/components/FileUpload';
import { ChatInput } from './ChatInput';
import classes from './ChatLandingView.module.scss';

export function ChatLandingView() {
  const { agent } = useAgentRun();

  return (
    <FileUpload>
      <Container size="sm" className={classes.root}>
        <div className={classes.header}>
          <AgentHeading agent={agent} />

          <AgentGreeting agent={agent} />
        </div>

        <ChatInput />
      </Container>
    </FileUpload>
  );
}

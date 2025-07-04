/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Container } from '#components/layouts/Container.tsx';
import { AgentHeading } from '#modules/agents/components/AgentHeading.tsx';

import { NewSessionButton } from '../components/NewSessionButton';
import { useAgentRun } from '../contexts/agent-run';
import { useMessages } from '../contexts/messages';
import { MessageTrajectories } from '../trajectory/components/MessageTrajectories';
import { isAgentMessage } from '../utils';
import classes from './HandsOffOutputView.module.scss';
import { HandsOffText } from './HandsOffText';
import { TaskStatusBar } from './TaskStatusBar';

export function HandsOffOutputView() {
  const { agent, input, isPending, cancel, clear } = useAgentRun();
  const { messages } = useMessages();
  const message = messages.find(isAgentMessage);

  return (
    <div className={classes.root}>
      <Container size="md" className={classes.holder}>
        <header className={classes.header}>
          <p className={classes.input}>{input}</p>

          <NewSessionButton onClick={clear} />
        </header>

        <div className={classes.body}>
          <AgentHeading agent={agent} />

          {message && (
            <>
              <HandsOffText message={message} />

              <MessageTrajectories message={message} />
            </>
          )}

          {isPending && (
            <div className={classes.statusBar}>
              <TaskStatusBar onStopClick={cancel} />
            </div>
          )}
        </div>
      </Container>
    </div>
  );
}

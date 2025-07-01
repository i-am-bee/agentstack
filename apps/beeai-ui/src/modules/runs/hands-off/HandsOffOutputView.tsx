/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Container } from '#components/layouts/Container.tsx';
import { AgentHeading } from '#modules/agents/components/AgentHeading.tsx';

import { AgentRunLogs } from '../components/AgentRunLogs';
import { NewSessionButton } from '../components/NewSessionButton';
import { useHandsOff } from '../contexts/hands-off';
import { useMessages } from '../contexts/messages';
import classes from './HandsOffOutputView.module.scss';
import { HandsOffText } from './HandsOffText';
import { TaskStatusBar } from './TaskStatusBar';
import { getHandsOffOutput } from './utils';

export function HandsOffOutputView() {
  const { agent, input, logs, isPending, onCancel, onClear } = useHandsOff();
  const { messages } = useMessages();
  const output = getHandsOffOutput(messages);

  const hasOutput = Boolean(output);

  return (
    <div className={classes.root}>
      <Container size="md" className={classes.holder}>
        <header className={classes.header}>
          <p className={classes.input}>{input}</p>

          <NewSessionButton onClick={onClear} />
        </header>

        <div className={classes.body}>
          <AgentHeading agent={agent} />

          <HandsOffText />

          {logs && <AgentRunLogs logs={logs} toggleable={hasOutput} />}

          {isPending && (
            <div className={classes.statusBar}>
              <TaskStatusBar onStopClick={onCancel} />
            </div>
          )}
        </div>
      </Container>
    </div>
  );
}

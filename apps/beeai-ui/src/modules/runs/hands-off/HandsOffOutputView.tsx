/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Container } from '#components/layouts/Container.tsx';
import { checkMessageContent, isAgentMessage } from '#modules/messages/utils.ts';

import { useMessages } from '../../messages/contexts';
import { MessageTrajectories } from '../../trajectories/components/MessageTrajectories';
import { NewSessionButton } from '../components/NewSessionButton';
import { useAgentRun } from '../contexts/agent-run';
import classes from './HandsOffOutputView.module.scss';
import { HandsOffText } from './HandsOffText';
import { TaskStatusBar } from './TaskStatusBar';

export function HandsOffOutputView() {
  const { input, isPending, cancel, clear } = useAgentRun();
  const { messages } = useMessages();

  const message = messages.find(isAgentMessage);
  const hasOutput = message ? checkMessageContent(message) : false;
  const containerSize = hasOutput ? 'md' : 'sm';

  return (
    <div className={classes.root}>
      <Container size={containerSize} className={classes.holder}>
        <header className={classes.header}>
          <div className={classes.headerContainer}>
            <p className={classes.input}>{input}</p>

            <NewSessionButton onClick={clear} />
          </div>
        </header>

        <div className={classes.body}>
          {message && (
            <>
              <HandsOffText message={message} className={classes.text} />

              <MessageTrajectories message={message} toggleable={hasOutput} autoScroll={!hasOutput} />
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

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use client';

import { ArrowDown } from '@carbon/icons-react';
import { IconButton } from '@carbon/react';

import { Container } from '#components/layouts/Container.tsx';
import { useIsScrolled } from '#hooks/useIsScrolled.ts';
import { isAgentMessage, isUserMessage } from '#modules/messages/utils.ts';

import { FileUpload } from '../../files/components/FileUpload';
import { useMessages } from '../../messages/contexts';
import { NewSessionButton } from '../components/NewSessionButton';
import { RunInput } from '../components/RunInput';
import { RunStatusBar } from '../components/RunStatusBar';
import { useAgentRun } from '../contexts/agent-run';
import { useAgentStatus } from '../contexts/agent-status';
import { ChatAgentMessage } from './ChatAgentMessage';
import classes from './ChatMessagesView.module.scss';
import { ChatUserMessage } from './ChatUserMessage';

export function ChatMessagesView() {
  const { scrollElementRef, observeElementRef, isScrolled, scrollToBottom } = useIsScrolled();
  const { isPending, clear } = useAgentRun();
  const { messages } = useMessages();
  const {
    status: { isNotInstalled, isStarting },
  } = useAgentStatus();

  return (
    <FileUpload>
      <div className={classes.holder}>
        <div className={classes.scrollable} ref={scrollElementRef}>
          <Container size="sm" className={classes.container}>
            <header className={classes.header}>
              <NewSessionButton onClick={clear} />
            </header>

            <ol className={classes.messages} aria-label="messages">
              {messages.map((message) => {
                const isUser = isUserMessage(message);
                const isAgent = isAgentMessage(message);

                return (
                  <li key={message.id} className={classes.message}>
                    {isUser && <ChatUserMessage message={message} />}

                    {isAgent && <ChatAgentMessage message={message} />}
                  </li>
                );
              })}
            </ol>

            <div className={classes.scrollRef} ref={observeElementRef} />
          </Container>
        </div>

        <div className={classes.bottom}>
          {isScrolled && (
            <IconButton
              label="Scroll to bottom"
              kind="secondary"
              size="sm"
              wrapperClasses={classes.toBottomButton}
              onClick={scrollToBottom}
              autoAlign
            >
              <ArrowDown />
            </IconButton>
          )}

          <div className={classes.bottomHolder}>
            <Container size="sm" className={classes.bottomContainer}>
              {isPending && (isNotInstalled || isStarting) ? (
                <RunStatusBar isPending>Starting the agent, please bee patient&hellip;</RunStatusBar>
              ) : (
                <RunInput
                  onSubmit={() => {
                    requestAnimationFrame(() => {
                      scrollToBottom();
                    });
                  }}
                />
              )}
            </Container>
          </div>
        </div>
      </div>
    </FileUpload>
  );
}

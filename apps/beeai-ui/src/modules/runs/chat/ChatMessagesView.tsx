/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use client';

import { ArrowDown } from '@carbon/icons-react';
import { IconButton } from '@carbon/react';
import { useCallback, useEffect, useRef, useState } from 'react';

import { Container } from '#components/layouts/Container.tsx';
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
  const scrollRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const [isScrolled, setIsScrolled] = useState(false);

  const { isPending, clear } = useAgentRun();
  const { messages } = useMessages();
  const {
    status: { isNotInstalled, isStarting },
  } = useAgentStatus();

  const scrollToBottom = useCallback(() => {
    const scrollElement = scrollRef.current;

    if (!scrollElement) {
      return;
    }

    scrollElement.scrollTo({
      top: scrollElement.scrollHeight,
    });

    setIsScrolled(false);
  }, []);

  useEffect(() => {
    const bottomElement = bottomRef.current;

    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsScrolled(!entry.isIntersecting);
      },
      { root: scrollRef.current },
    );

    if (bottomElement) {
      observer.observe(bottomElement);
    }

    return () => {
      if (bottomElement) {
        observer.unobserve(bottomElement);
      }
    };
  }, []);

  return (
    <FileUpload>
      <div className={classes.holder}>
        <div className={classes.scrollable} ref={scrollRef}>
          <Container size="sm" className={classes.container}>
            <header className={classes.header}>
              <NewSessionButton onClick={clear} />
            </header>

            <ol className={classes.messages} aria-label="messages">
              {messages.map((message) => {
                const isUser = isUserMessage(message);
                const isAgent = isAgentMessage(message);

                return (
                  <li key={message.id}>
                    {isUser && <ChatUserMessage message={message} />}

                    {isAgent && <ChatAgentMessage message={message} />}
                  </li>
                );
              })}
            </ol>

            <div className={classes.scrollRef} ref={bottomRef} />
          </Container>
        </div>

        <Container size="sm" className={classes.bottom}>
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
    </FileUpload>
  );
}

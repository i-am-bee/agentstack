/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ArrowDown } from '@carbon/icons-react';
import { IconButton } from '@carbon/react';
import { useCallback, useEffect, useRef, useState } from 'react';

import { Container } from '#components/layouts/Container.tsx';

import { NewSessionButton } from '../components/NewSessionButton';
import { StatusBar } from '../components/StatusBar';
import { useAgent } from '../contexts/agent';
import { useChat } from '../contexts/chat';
import { useMessages } from '../contexts/messages';
import { FileUpload } from '../files/components/FileUpload';
import { ChatInput } from './ChatInput';
import classes from './ChatMessagesView.module.scss';
import { Message } from './Message';

export function ChatMessagesView() {
  const scrollRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const [isScrolled, setIsScrolled] = useState(false);

  const { isPending, onClear } = useChat();
  const { messages } = useMessages();
  const {
    status: { isNotInstalled, isStarting },
  } = useAgent();

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
        <Container size="sm" asChild>
          <header className={classes.header}>
            <NewSessionButton onClick={onClear} />
          </header>
        </Container>

        <div className={classes.scrollable} ref={scrollRef}>
          <div className={classes.scrollRef} ref={bottomRef} />

          <Container size="sm" asChild>
            <ol className={classes.messages} aria-label="messages">
              {messages.map((message) => (
                <Message key={message.key} message={message} />
              ))}
            </ol>
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
            <StatusBar isPending>Starting the agent, please bee patient&hellip;</StatusBar>
          ) : (
            <ChatInput
              onMessageSubmit={() => {
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

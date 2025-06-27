/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ArrowDown } from '@carbon/icons-react';
import { IconButton } from '@carbon/react';
import { useCallback, useEffect, useRef, useState } from 'react';

import { Container } from '#components/layouts/Container.tsx';

import { AgentHeader } from '../components/AgentHeader';
import { StatusBar } from '../components/StatusBar';
import { useAgent } from '../contexts/agent';
import { useChat, useChatMessages } from '../contexts/chat';
import { FileUpload } from '../files/components/FileUpload';
import { ChatInput } from './ChatInput';
import classes from './ChatMessagesView.module.scss';
import { Message } from './Message';

export function ChatMessagesView() {
  const scrollRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const [isScrolled, setIsScrolled] = useState(false);

  const { isPending, onClear } = useChat();
  const messages = useChatMessages();
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
      <Container size="sm" className={classes.holder}>
        <AgentHeader onNewSessionClick={onClear} />

        <div className={classes.content} ref={scrollRef}>
          <div className={classes.scrollRef} ref={bottomRef} />

          <ol className={classes.messages} aria-label="messages">
            {messages.map((message) => (
              <Message key={message.key} message={message} />
            ))}
          </ol>
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
        </div>
      </Container>
    </FileUpload>
  );
}

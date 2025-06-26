/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { ArrowDown } from '@carbon/icons-react';
import { IconButton } from '@carbon/react';
import clsx from 'clsx';
import { useCallback, useEffect, useRef, useState } from 'react';

import { Container } from '#components/layouts/Container.tsx';
import { AgentGreeting } from '#modules/agents/components/AgentGreeting.tsx';

import { AgentHeader } from '../components/AgentHeader';
import { AgentIcon } from '../components/AgentIcon';
import { StatusBar } from '../components/StatusBar';
import { useAgent } from '../contexts/agent';
import { useChat, useChatMessages } from '../contexts/chat';
import { FileUploadDropzone } from '../files/components/FileUploadDropzone';
import { useFileUpload } from '../files/contexts';
import classes from './Chat.module.scss';
import { ChatInput } from './ChatInput';
import { ChatView } from './ChatView';
import { Message } from './Message';

export function Chat() {
  const scrollRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const [isScrolled, setIsScrolled] = useState(false);

  const { dropzone } = useFileUpload();
  const { agent, onClear, isPending } = useChat();
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

  const isNew = !(isPending || messages.length);

  useEffect(() => {
    if (isNew) return;

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
  }, [isNew]);

  const className = clsx(classes.root, { [classes.isNew]: isNew });

  return (
    <ChatView>
      <div {...(dropzone ? dropzone.getRootProps({ className }) : { className })}>
        <Container size="sm" className={classes.holder}>
          {isNew ? (
            <div className={classes.header}>
              <AgentIcon size="xl" />
              <AgentGreeting agent={agent} />
            </div>
          ) : (
            <AgentHeader className={classes.header} onNewSessionClick={onClear} />
          )}

          {!isNew && (
            <div className={classes.content} ref={scrollRef}>
              <div className={classes.scrollRef} ref={bottomRef} />

              <ol className={classes.messages} aria-label="messages">
                {messages.map((message) => (
                  <Message key={message.key} message={message} />
                ))}
              </ol>
            </div>
          )}

          <div className={classes.bottom}>
            {!isNew && isScrolled && (
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

        {dropzone?.isDragActive && <FileUploadDropzone />}
      </div>
    </ChatView>
  );
}

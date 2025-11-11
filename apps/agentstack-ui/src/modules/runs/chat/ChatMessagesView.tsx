/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use client';
import { ArrowDown } from '@carbon/icons-react';
import { IconButton, InlineLoading } from '@carbon/react';
import { useRouter } from 'next/navigation';

import { Container } from '#components/layouts/Container.tsx';
import { useIsScrolled } from '#hooks/useIsScrolled.ts';
import { isAgentMessage, isUserMessage } from '#modules/messages/utils.ts';
import { routes } from '#utils/router.ts';

import { FileUpload } from '../../files/components/FileUpload';
import { useMessages } from '../../messages/contexts/Messages';
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
  const { agent, isPending } = useAgentRun();
  const {
    messages,
    queryControl: { hasNextPage, fetchNextPageInViewAnchorRef, isFetchingNextPage },
  } = useMessages();
  const {
    status: { isNotInstalled, isStarting },
  } = useAgentStatus();
  const router = useRouter();

  const showScrollToBottom = messages.length > 0 && isScrolled;

  return (
    <FileUpload>
      <div className={classes.holder}>
        <div className={classes.scrollable} ref={scrollElementRef}>
          <Container size="sm" className={classes.container}>
            <header className={classes.header}>
              <NewSessionButton
                onClick={() => {
                  router.push(routes.agentRun({ providerId: agent.provider.id }));
                }}
              />
            </header>

            <ol className={classes.messages} aria-label="messages">
              {messages.map((message, idx) => {
                const isUser = isUserMessage(message);
                const isAgent = isAgentMessage(message);

                // messages are displayed in reverse order
                const isLast = idx === 0;
                const isFirst = idx === messages.length - 1;

                return (
                  <li key={message.id}>
                    {isUser && <ChatUserMessage message={message} />}

                    {isAgent && (
                      <ChatAgentMessage
                        message={message}
                        isLast={isLast}
                        isFirst={isFirst}
                        containerScrollableRef={scrollElementRef}
                      />
                    )}

                    {isLast && <div ref={observeElementRef} />}
                    {isFirst && hasNextPage && <div ref={fetchNextPageInViewAnchorRef} />}
                  </li>
                );
              })}

              {isFetchingNextPage && (
                <li className={classes.loading}>
                  <InlineLoading description="Loading more messages..." />
                </li>
              )}
            </ol>
          </Container>
        </div>

        <div className={classes.bottom}>
          {showScrollToBottom && (
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
                <RunInput />
              )}
            </Container>
          </div>
        </div>
      </div>
    </FileUpload>
  );
}

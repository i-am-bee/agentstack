/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';

import { getErrorMessage } from '#api/utils.ts';
import { ErrorMessage } from '#components/ErrorMessage/ErrorMessage.tsx';
import { MarkdownContent } from '#components/MarkdownContent/MarkdownContent.tsx';
import { Spinner } from '#components/Spinner/Spinner.tsx';
import { getAgentUiMetadata } from '#modules/agents/utils.ts';

import { AgentIcon } from '../components/AgentIcon';
import { useChat } from '../contexts/chat';
import { FileCard } from '../files/components/FileCard';
import { FileCardsList } from '../files/components/FileCardsList';
import { Role } from '../types';
import classes from './Message.module.scss';
import { type ChatMessage, MessageStatus } from './types';
import { UserIcon } from './UserIcon';

interface Props {
  message: ChatMessage;
}

export function Message({ message }: Props) {
  const { agent } = useChat();
  const { content, role, error } = message;

  const { display_name } = getAgentUiMetadata(agent);

  const isUserMessage = role === Role.User;
  const isAssistantMessage = role === Role.Assistant;
  const isPending = isAssistantMessage && message.status === MessageStatus.InProgress && !content;
  const isError =
    isAssistantMessage && (message.status === MessageStatus.Failed || message.status === MessageStatus.Aborted);
  const isFailed = isAssistantMessage && message.status === MessageStatus.Failed;

  const files = message.files ?? [];

  const hasFiles = files.length > 0;

  return (
    <li className={clsx(classes.root)}>
      <div className={classes.sender}>
        <div className={classes.senderIcon}>{isUserMessage ? <UserIcon /> : <AgentIcon />}</div>
        <div className={classes.senderName}>{isUserMessage ? 'User' : display_name}</div>
      </div>

      <div className={classes.body}>
        {isPending ? (
          <Spinner />
        ) : isError ? (
          <ErrorMessage
            title={isFailed ? 'Failed to generate an assistant message.' : 'Message generation has been cancelled.'}
            subtitle={getErrorMessage(error)}
          />
        ) : (
          <div className={clsx(classes.content, { [classes.isUser]: isUserMessage })}>
            {content ? (
              <MarkdownContent>{content}</MarkdownContent>
            ) : (
              <span className={classes.empty}>Message has no content</span>
            )}
          </div>
        )}

        {hasFiles && (
          <FileCardsList>
            {files.map(({ key, filename, href }) => (
              <li key={key}>
                <FileCard href={href} filename={filename} />
              </li>
            ))}
          </FileCardsList>
        )}
      </div>
    </li>
  );
}

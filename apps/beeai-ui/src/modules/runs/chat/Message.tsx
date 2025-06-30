/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import { useCallback } from 'react';

import { getErrorMessage } from '#api/utils.ts';
import { ErrorMessage } from '#components/ErrorMessage/ErrorMessage.tsx';
import { MarkdownContent } from '#components/MarkdownContent/MarkdownContent.tsx';
import { Spinner } from '#components/Spinner/Spinner.tsx';
import { useApp } from '#contexts/App/index.ts';
import { getAgentUiMetadata } from '#modules/agents/utils.ts';

import { AgentIcon } from '../components/AgentIcon';
import { useChat } from '../contexts/chat';
import { FileCard } from '../files/components/FileCard';
import { FileCardsList } from '../files/components/FileCardsList';
import { SourcesButton } from '../sources/components/SourcesButton';
import { useSources } from '../sources/contexts';
import { TrajectoryView } from '../trajectory/components/TrajectoryView';
import { Role } from '../types';
import { isAgentMessage } from '../utils';
import classes from './Message.module.scss';
import { type ChatMessage, MessageStatus } from './types';
import { UserIcon } from './UserIcon';

interface Props {
  message: ChatMessage;
}

export function Message({ message }: Props) {
  const { agent } = useChat();
  const { sourcesPanelOpen, showSourcesPanel, hideSourcesPanel } = useApp();
  const { activeMessageKey, setActiveMessageKey, setActiveSourceKey } = useSources();
  const { key, content, role, error } = message;

  const { display_name } = getAgentUiMetadata(agent);

  const isUserMessage = role === Role.User;
  const isAssistantMessage = isAgentMessage(message);
  const isPending = isAssistantMessage && message.status === MessageStatus.InProgress && !content;
  const isError =
    isAssistantMessage && (message.status === MessageStatus.Failed || message.status === MessageStatus.Aborted);
  const isFailed = isAssistantMessage && message.status === MessageStatus.Failed;

  const files = message.files ?? [];
  const sources = (isAssistantMessage ? message.sources : null) ?? [];
  const trajectories = (isAssistantMessage ? message.trajectories : null) ?? [];

  const hasFiles = files.length > 0;
  const hasSources = isAssistantMessage && sources.length > 0;
  const hasTrajectories = trajectories.length > 0;

  const isSourcesActive = sourcesPanelOpen && activeMessageKey === key;

  const handleSourcesButtonClick = useCallback(() => {
    if (key === activeMessageKey) {
      if (sourcesPanelOpen) {
        hideSourcesPanel?.();
      } else {
        showSourcesPanel?.();
      }
    } else {
      setActiveMessageKey?.(key);
      setActiveSourceKey?.(null);
      showSourcesPanel?.();
    }
  }, [
    key,
    activeMessageKey,
    sourcesPanelOpen,
    hideSourcesPanel,
    showSourcesPanel,
    setActiveMessageKey,
    setActiveSourceKey,
  ]);

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
              <MarkdownContent sources={sources}>{content}</MarkdownContent>
            ) : (
              <span className={classes.empty}>Message has no content</span>
            )}
          </div>
        )}

        {hasFiles && (
          <FileCardsList className={classes.files}>
            {files.map(({ key, filename, href }) => (
              <li key={key}>
                <FileCard href={href} filename={filename} />
              </li>
            ))}
          </FileCardsList>
        )}

        {hasSources && (
          <SourcesButton sources={sources} isActive={isSourcesActive} onClick={handleSourcesButtonClick} />
        )}

        {hasTrajectories && <TrajectoryView trajectories={trajectories} />}
      </div>
    </li>
  );
}

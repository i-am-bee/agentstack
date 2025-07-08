/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { MarkdownContent } from '#components/MarkdownContent/MarkdownContent.tsx';

import type { ChatMessage } from '../chat/types';
import { useAgentRun } from '../contexts/agent-run';
import { isAgentMessage } from '../utils';
import classes from './MessageContent.module.scss';

interface Props {
  message: ChatMessage;
}

export function MessageContent({ message }: Props) {
  const { content } = message;
  const { isPending } = useAgentRun();
  const isAgent = isAgentMessage(message);
  const sources = (isAgent ? message.sources : null) ?? [];

  return content ? (
    <MarkdownContent sources={sources} isPending={isPending}>
      {content}
    </MarkdownContent>
  ) : (
    <div className={classes.empty}>Message has no content</div>
  );
}

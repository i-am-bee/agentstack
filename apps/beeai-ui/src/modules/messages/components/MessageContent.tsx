/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';

import { MarkdownContent } from '#components/MarkdownContent/MarkdownContent.tsx';
import type { UIMessage } from '#modules/messages/types.ts';

import { useAgentRun } from '../../runs/contexts/agent-run';
import { getMessageContent, getMessageSources } from '../utils';
import classes from './MessageContent.module.scss';

interface Props {
  message: UIMessage;
}

export function MessageContent({ message }: Props) {
  const { isPending } = useAgentRun();

  const content = getMessageContent(message);
  const sources = getMessageSources(message);

  return content ? (
    <MarkdownContent className={classes.root} sources={sources} isPending={isPending}>
      {content}
    </MarkdownContent>
  ) : (
    <div className={clsx(classes.empty, classes.root)}>Message has no content</div>
  );
}

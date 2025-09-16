/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import { memo } from 'react';

import { MarkdownContent } from '#components/MarkdownContent/MarkdownContent.tsx';
import type { UIMessage } from '#modules/messages/types.ts';

import { useAgentRun } from '../../runs/contexts/agent-run';
import { Role } from '../api/types';
import { getMessageContent, getMessageSources } from '../utils';
import classes from './MessageContent.module.scss';
import { MessageFormResponse } from './MessageFormResponse';

interface Props {
  message: UIMessage;
}

export const MessageContent = memo(function MessageContent({ message }: Props) {
  const { isPending } = useAgentRun();

  const content = getMessageContent(message);
  const form = message.role === Role.User ? message.form : null;
  const auth = message.role === Role.User ? message.auth : null;
  const hasContent = content || form || auth;
  const sources = getMessageSources(message);

  if (hasContent) {
    if (form) {
      return <MessageFormResponse form={form} />;
    }

    if (auth) {
      return <div className={clsx(classes.root)}>User has granted access</div>;
    }

    return (
      <MarkdownContent className={classes.root} sources={sources} isPending={isPending}>
        {content}
      </MarkdownContent>
    );
  } else {
    return <div className={clsx(classes.empty, classes.root)}>Message has no content</div>;
  }
});

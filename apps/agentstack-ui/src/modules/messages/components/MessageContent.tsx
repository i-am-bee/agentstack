/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import { memo } from 'react';

import { LineClampText } from '#components/LineClampText/LineClampText.tsx';
import type { UIMessage } from '#modules/messages/types.ts';
import { ChatMarkdownContent } from '#modules/runs/components/ChatMarkdownContent/ChatMarkdownContent.tsx';

import {
  checkMessageStatus,
  getMessageContent,
  getMessageSecret,
  getMessageSources,
  isAgentMessage,
  isUserMessage,
} from '../utils';
import classes from './MessageContent.module.scss';
import { MessageFormResponse } from './MessageFormResponse';

interface Props {
  message: UIMessage;
}

export const MessageContent = memo(function MessageContent({ message }: Props) {
  const content = getMessageContent(message);
  const isUser = isUserMessage(message);
  const form = isUser ? message.form : null;
  const auth = isUser ? message.auth : null;
  const canvasEditRequest = isUser ? message.canvasEditRequest : null;
  const secretPart = getMessageSecret(message);

  const hasContent = content || form || auth || canvasEditRequest;
  const sources = getMessageSources(message);

  const status = isAgentMessage(message) ? checkMessageStatus(message) : null;

  if (hasContent) {
    if (form) {
      return <MessageFormResponse form={form} />;
    }

    if (auth) {
      return <div className={clsx(classes.root)}>User has granted access</div>;
    }

    if (canvasEditRequest) {
      return (
        <div className={clsx(classes.root, classes.canvasEditRequest)}>
          <LineClampText lines={2}>
            <q>{canvasEditRequest.content}</q>
          </LineClampText>
          <p>{canvasEditRequest.description}</p>
        </div>
      );
    }

    return (
      <ChatMarkdownContent
        className={classes.root}
        sources={sources}
        codeBlocksExpanded={status?.isInProgress}
        isStreaming={status?.isInProgress}
      >
        {content}
      </ChatMarkdownContent>
    );
  } else if (secretPart || status?.isError) {
    return null;
  } else {
    return <div className={clsx(classes.empty, classes.root)}>Message has no content</div>;
  }
});

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { MessageFiles } from '#modules/files/components/MessageFiles.tsx';
import { MessageContent } from '#modules/messages/components/MessageContent.tsx';
import type { UIUserMessage } from '#modules/messages/types.ts';

import classes from './ChatUserMessage.module.scss';

interface Props {
  message: UIUserMessage;
}

export function ChatUserMessage({ message }: Props) {
  return (
    <div className={classes.root}>
      <div className={classes.content}>
        <MessageContent message={message} />
      </div>

      <MessageFiles message={message} className={classes.files} />
    </div>
  );
}

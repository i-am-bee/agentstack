/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { LineClampText } from '#components/LineClampText/LineClampText.tsx';
import { MessageFiles } from '#modules/files/components/MessageFiles.tsx';
import { MessageContent } from '#modules/messages/components/MessageContent.tsx';
import type { UIUserMessage } from '#modules/messages/types.ts';

import classes from './ChatUserMessage.module.scss';

interface Props {
  message: UIUserMessage;
}

export function ChatUserMessage({ message }: Props) {
  const { runtimeFullfilledDemands } = message;

  if (runtimeFullfilledDemands) {
    return null;
  }

  return (
    <div className={classes.root}>
      <div className={classes.content}>
        <LineClampText lines={3} buttonClassName={classes.moreButton} iconButton useBlockElement>
          <MessageContent message={message} />
        </LineClampText>
      </div>

      <MessageFiles message={message} className={classes.files} />
    </div>
  );
}

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Spinner } from '#components/Spinner/Spinner.tsx';
import { MessageFiles } from '#modules/files/components/MessageFiles.tsx';
import { MessageContent } from '#modules/messages/components/MessageContent.tsx';
import { MessageError } from '#modules/messages/components/MessageError.tsx';
import type { UIAgentMessage } from '#modules/messages/types.ts';
import { checkMessageContent, checkMessageStatus } from '#modules/messages/utils.ts';
import { MessageSources } from '#modules/sources/components/MessageSources.tsx';
import { MessageTrajectories } from '#modules/trajectories/components/MessageTrajectories.tsx';

import classes from './ChatAgentMessage.module.scss';

interface Props {
  message: UIAgentMessage;
}

export function ChatAgentMessage({ message }: Props) {
  const hasContent = checkMessageContent(message);
  const { isInProgress } = checkMessageStatus(message);
  const isPending = isInProgress && !hasContent;

  return (
    <div className={classes.root}>
      {isPending ? (
        <Spinner />
      ) : (
        <>
          <div className={classes.content}>
            <MessageContent message={message} />
          </div>

          <MessageError message={message} />
        </>
      )}

      <MessageFiles message={message} />

      <MessageSources message={message} />

      <MessageTrajectories message={message} />
    </div>
  );
}

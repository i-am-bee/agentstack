/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useRef } from 'react';

import { Spinner } from '#components/Spinner/Spinner.tsx';
import { MessageFiles } from '#modules/files/components/MessageFiles.tsx';
import { MessageForm } from '#modules/form/components/MessageForm.tsx';
import { MessageActions } from '#modules/messages/components/MessageActions.tsx';
import { MessageContent } from '#modules/messages/components/MessageContent.tsx';
import { MessageError } from '#modules/messages/components/MessageError.tsx';
import { useMessageInteractionPropsContext } from '#modules/messages/contexts/MessageInteraction/index.ts';
import { MessageInteractionProvider } from '#modules/messages/contexts/MessageInteraction/MessageInteractionProvider.tsx';
import type { UIAgentMessage } from '#modules/messages/types.ts';
import { checkMessageContent, checkMessageStatus } from '#modules/messages/utils.ts';
import { MessageSources } from '#modules/sources/components/MessageSources.tsx';
import { MessageTrajectories } from '#modules/trajectories/components/MessageTrajectories.tsx';

import classes from './ChatAgentMessage.module.scss';

interface Props {
  message: UIAgentMessage;
}

export function ChatAgentMessage({ message }: Props) {
  return (
    <MessageInteractionProvider>
      <Message message={message} />
    </MessageInteractionProvider>
  );
}

function Message({ message }: Props) {
  const contentRef = useRef<HTMLDivElement>(null);

  const { props } = useMessageInteractionPropsContext();

  const hasContent = checkMessageContent(message);
  const { isInProgress } = checkMessageStatus(message);
  const isPending = isInProgress && !hasContent;

  return (
    <div {...props} className={classes.root}>
      {isPending ? (
        <Spinner center />
      ) : (
        <>
          <div className={classes.content} ref={contentRef}>
            <MessageContent message={message} />
          </div>

          <MessageError message={message} />
        </>
      )}

      <MessageFiles message={message} />

      <MessageSources message={message} />

      <MessageTrajectories message={message} />

      <MessageForm message={message} />

      <MessageForm message={message} />

      {!isPending && <MessageActions message={message} className={classes.actions} contentRef={contentRef} />}
    </div>
  );
}

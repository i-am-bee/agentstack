/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { rem } from '@carbon/layout';
import { useCallback, useEffect, useRef } from 'react';

import { Spinner } from '#components/Spinner/Spinner.tsx';
import { MessageFiles } from '#modules/files/components/MessageFiles.tsx';
import { MessageAuth } from '#modules/form/components/MessageAuth.tsx';
import { MessageForm } from '#modules/form/components/MessageForm.tsx';
import { MessageSecretsForm } from '#modules/form/components/MessageSecretsForm.tsx';
import { MessageActions } from '#modules/messages/components/MessageActions.tsx';
import { MessageContent } from '#modules/messages/components/MessageContent.tsx';
import { MessageError } from '#modules/messages/components/MessageError.tsx';
import { useMessageInteractionProps } from '#modules/messages/contexts/MessageInteraction/index.ts';
import { MessageInteractionProvider } from '#modules/messages/contexts/MessageInteraction/MessageInteractionProvider.tsx';
import type { UIAgentMessage } from '#modules/messages/types.ts';
import { checkMessageContent, checkMessageStatus } from '#modules/messages/utils.ts';
import { MessageSources } from '#modules/sources/components/MessageSources.tsx';
import { MessageTrajectories } from '#modules/trajectories/components/MessageTrajectories.tsx';

import classes from './ChatAgentMessage.module.scss';

interface Props {
  message: UIAgentMessage;
  isLast?: boolean;
  containerScrollableRef?: React.RefObject<HTMLDivElement>;
  onShow?: () => void;
}

export function ChatAgentMessage(props: Props) {
  return (
    <MessageInteractionProvider>
      <Message {...props} />
    </MessageInteractionProvider>
  );
}

function Message({ message, isLast, containerScrollableRef, onShow }: Props) {
  const contentRef = useRef<HTMLDivElement>(null);
  const rootRef = useRef<HTMLDivElement>(null);

  const { props } = useMessageInteractionProps();

  useEffect(() => {
    onShow?.();
  }, [onShow]);

  const updateHeight = useCallback(() => {
    if (!containerScrollableRef?.current || !rootRef.current) {
      return;
    }

    if (!isLast) {
      rootRef.current.style.minBlockSize = '';
      return;
    } else {
      const containerHeight = containerScrollableRef.current.clientHeight;
      const listItem = rootRef.current.closest('li');
      const prevMessageElem = listItem?.nextElementSibling; // Messages are in reverse order

      if (prevMessageElem instanceof HTMLElement) {
        const nextSiblingHeight = prevMessageElem?.offsetHeight ?? 0;

        const availableHeight = containerHeight - nextSiblingHeight - MESSAGES_GAP;
        rootRef.current.style.minBlockSize = rem(availableHeight);
      }
    }
  }, [isLast, containerScrollableRef]);

  useEffect(() => {
    updateHeight();

    // Update height on window resize
    window.addEventListener('resize', updateHeight);
    return () => window.removeEventListener('resize', updateHeight);
  }, [isLast, updateHeight]);

  const hasContent = checkMessageContent(message);
  const { isInProgress } = checkMessageStatus(message);
  const isPending = isInProgress && !hasContent;

  return (
    <div {...props} className={classes.root} ref={rootRef}>
      {isPending && (
        <div className={classes.spinner}>
          <Spinner center />
        </div>
      )}

      <MessageTrajectories message={message} autoScroll={isPending} toggleable={!isPending} />

      {!isPending && (
        <>
          <div className={classes.content} ref={contentRef}>
            <MessageContent message={message} />
          </div>

          <MessageError message={message} />
        </>
      )}

      <MessageFiles message={message} />

      <MessageSources message={message} />

      <MessageForm message={message} />

      <MessageAuth message={message} />

      <MessageSecretsForm message={message} />

      {!isPending && <MessageActions message={message} className={classes.actions} contentRef={contentRef} />}
    </div>
  );
}

const MESSAGES_GAP = 2 * 16; // 2rem

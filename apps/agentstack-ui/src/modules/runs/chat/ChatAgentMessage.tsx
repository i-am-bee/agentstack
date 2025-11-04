/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { rem } from '@carbon/layout';
import type { RefObject } from 'react';
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
  isFirst?: boolean;
  containerScrollableRef?: RefObject<HTMLDivElement | null>;
}

export function ChatAgentMessage(props: Props) {
  return (
    <MessageInteractionProvider>
      <Message {...props} />
    </MessageInteractionProvider>
  );
}

function Message({ message, isLast, isFirst, containerScrollableRef }: Props) {
  const contentRef = useRef<HTMLDivElement>(null);
  const rootRef = useRef<HTMLDivElement>(null);

  const { props } = useMessageInteractionProps();

  const updateHeight = useCallback(() => {
    if (!containerScrollableRef?.current || !rootRef.current) {
      return;
    }

    if (!isLast) {
      rootRef.current.style.minBlockSize = '';
      return;
    } else {
      const containerHeight = containerScrollableRef.current.clientHeight;
      const listItemElem = rootRef.current.parentElement;
      const messagesElem = listItemElem?.parentElement;
      const prevMessageElem = listItemElem?.nextElementSibling; // Messages are in reverse order

      if (messagesElem) {
        const nextSiblingHeight =
          prevMessageElem instanceof HTMLLIElement
            ? prevMessageElem.offsetHeight
            : isFirst
              ? MESSAGE_PLACEHOLDER_HEIGHT
              : 0;
        const rowGap = nextSiblingHeight ? parseFloat(window.getComputedStyle(messagesElem).rowGap) : 0;

        const availableHeight = Math.max(0, containerHeight - nextSiblingHeight - rowGap);
        rootRef.current.style.minBlockSize = rem(availableHeight);
      }
    }
  }, [containerScrollableRef, isLast, isFirst]);

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
    <div {...props} className={classes.root} ref={rootRef} data-last={isLast ? 'true' : 'false'}>
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

const MESSAGE_PLACEHOLDER_HEIGHT = 40;

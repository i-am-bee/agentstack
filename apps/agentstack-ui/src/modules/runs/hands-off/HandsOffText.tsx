/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useAutoScroll } from '#hooks/useAutoScroll.ts';
import type { UIAgentMessage } from '#modules/messages/types.ts';
import { checkMessageStatus, getMessageContent, getMessageSources } from '#modules/messages/utils.ts';
import { MessageSources } from '#modules/sources/components/MessageSources.tsx';

import { MessageFiles } from '../../files/components/MessageFiles';
import { MessageError } from '../../messages/components/MessageError';
import { RunOutputBox } from '../components/RunOutputBox';
import { useAgentRun } from '../contexts/agent-run';

interface Props {
  message: UIAgentMessage;
  className?: string;
}

export function HandsOffText({ message, className }: Props) {
  const { agent, isPending } = useAgentRun();

  const content = getMessageContent(message);
  const sources = getMessageSources(message);
  const { isError } = checkMessageStatus(message);

  const { ref: autoScrollRef } = useAutoScroll([content]);

  return content || isError ? (
    <div className={className}>
      <RunOutputBox sources={sources} text={content} isPending={isPending} downloadFileName={`${agent.name}-output`}>
        <MessageError message={message} />

        <MessageFiles message={message} />

        <MessageSources message={message} />
      </RunOutputBox>

      {isPending && <div ref={autoScrollRef} />}
    </div>
  ) : null;
}

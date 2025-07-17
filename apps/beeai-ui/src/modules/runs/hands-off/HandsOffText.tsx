/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useAutoScroll } from '#hooks/useAutoScroll.ts';

import { type AgentMessage, MessageStatus } from '../chat/types';
import { AgentOutputBox } from '../components/AgentOutputBox';
import { MessageError } from '../components/MessageError';
import { useAgentRun } from '../contexts/agent-run';
import { MessageFiles } from '../files/components/MessageFiles';
import { MessageSources } from '../sources/components/MessageSources';

interface Props {
  message: AgentMessage;
  className?: string;
}

export function HandsOffText({ message, className }: Props) {
  const { agent, isPending } = useAgentRun();
  const { content, status, sources = [] } = message;
  const { ref: autoScrollRef } = useAutoScroll([content]);

  const isError = status === MessageStatus.Failed || status === MessageStatus.Aborted;

  return content || isError ? (
    <div className={className}>
      <AgentOutputBox sources={sources} text={content} isPending={isPending} downloadFileName={`${agent.name}-output`}>
        {isError && <MessageError message={message} />}

        <MessageFiles message={message} />

        <MessageSources message={message} />
      </AgentOutputBox>

      {isPending && <div ref={autoScrollRef} />}
    </div>
  ) : null;
}

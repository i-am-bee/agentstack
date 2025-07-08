/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useAutoScroll } from '#hooks/useAutoScroll.ts';

import type { AgentMessage } from '../chat/types';
import { AgentOutputBox } from '../components/AgentOutputBox';
import { useAgentRun } from '../contexts/agent-run';
import { MessageFiles } from '../files/components/MessageFiles';
import { MessageSources } from '../sources/components/MessageSources';

interface Props {
  message: AgentMessage;
}

export function HandsOffText({ message }: Props) {
  const { agent, isPending } = useAgentRun();
  const output = message.content;
  const { ref: autoScrollRef } = useAutoScroll([output]);
  const sources = message.sources ?? [];

  return output ? (
    <div>
      <AgentOutputBox sources={sources} text={output} isPending={isPending} downloadFileName={`${agent.name}-output`}>
        <MessageFiles message={message} />

        <MessageSources message={message} />
      </AgentOutputBox>

      {isPending && <div ref={autoScrollRef} />}
    </div>
  ) : null;
}

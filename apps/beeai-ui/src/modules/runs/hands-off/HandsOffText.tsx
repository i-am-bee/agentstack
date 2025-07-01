/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useAutoScroll } from '#hooks/useAutoScroll.ts';

import { AgentOutputBox } from '../components/AgentOutputBox';
import { useHandsOff } from '../contexts/hands-off';
import { useMessages } from '../contexts/messages';
import { MessageFiles } from '../files/components/MessageFiles';
import { MessageSources } from '../sources/components/MessageSources';
import { isAgentMessage } from '../utils';

export function HandsOffText() {
  const { agent, isPending } = useHandsOff();
  const { messages } = useMessages();

  const message = messages.find(isAgentMessage);
  const output = message?.content;
  const { ref: autoScrollRef } = useAutoScroll([output]);

  const sources = message?.sources ?? [];

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

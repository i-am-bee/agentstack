/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { AgentCapabilities, Message } from '../../a2a/protocol/types';
import type { Fulfillments } from '../extensions/types';
import { handleAgentCard } from '../handle-agent-card';

export const buildMessageBuilder =
  (agent: { capabilities: AgentCapabilities }) =>
  async (
    contextId: string,
    fulfillments: Fulfillments,
    originalMessage: Pick<Message, 'parts' | 'messageId'>,
  ): Promise<Message> => {
    const { resolveMetadata } = handleAgentCard(agent);
    const metadata = await resolveMetadata(fulfillments);

    return {
      ...originalMessage,
      contextId,
      kind: 'message',
      role: 'user',
      metadata,
    } as const;
  };

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Client } from '@a2a-js/sdk/client';
import { buildLLMExtensionFulfillmentResolver, type ContextToken, handleAgentCard, type Message } from 'agentstack-sdk';

import { api } from './api';
import type { ChatMessage } from './types';

export function createMessage({ role, text }: Pick<ChatMessage, 'role' | 'text'>): ChatMessage {
  return {
    id: crypto.randomUUID(),
    role,
    text,
  };
}

export async function resolveAgentMetadata({ client, contextToken }: { client: Client; contextToken: ContextToken }) {
  const agentCard = await client.getAgentCard();
  const { resolveMetadata } = handleAgentCard(agentCard);
  const llmResolver = buildLLMExtensionFulfillmentResolver(api, contextToken);
  const agentMetadata = await resolveMetadata({ llm: llmResolver });

  return agentMetadata;
}

export function extractTextFromMessage(message: Message | undefined) {
  const text = message?.parts
    .filter((part) => part.kind === 'text')
    .map((part) => part.text)
    .join('\n');

  return text;
}

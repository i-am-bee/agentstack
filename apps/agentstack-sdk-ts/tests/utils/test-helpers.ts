/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { TextPart } from '@a2a-js/sdk';
import type { Client, TaskStatusUpdateEvent } from '@a2a-js/sdk/client';
import {
  ClientFactory,
  ClientFactoryOptions,
  DefaultAgentCardResolver,
  JsonRpcTransportFactory,
} from '@a2a-js/sdk/client';
import net from 'net';

import type { Fulfillments } from '../../src/client/core';
import { buildMessageBuilder, handleAgentCard } from '../../src/client/core';
import { Server, type ServerHandle } from '../../src/server';

export async function getRandomPort(): Promise<number> {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.listen(0, () => {
      const address = server.address();
      if (address && typeof address === 'object') {
        const port = address.port;
        server.close(() => resolve(port));
      } else {
        reject(new Error('Failed to get port'));
      }
    });
    server.on('error', reject);
  });
}

export async function createEchoAgent(port: number): Promise<ServerHandle> {
  const server = new Server();

  return server
    .agent({
      name: 'EchoAgent',
      description: 'An echo agent for testing',
      version: '1.0.0',
      handler: async function* (input) {
        const firstPart = input.parts?.[0] as TextPart | undefined;
        if (firstPart?.kind === 'text') {
          yield `Echo: ${firstPart.text}`;
        } else {
          yield 'No text part found';
        }
      },
    })
    .run({ port, host: '127.0.0.1' });
}

export function createTestFulfillments(): Fulfillments {
  return {
    getContextToken: () => ({ token: 'test-token', expires_at: null }),
    llm: async () => ({ llm_fulfillments: {} }),
    embedding: async () => ({ embedding_fulfillments: {} }),
    mcp: async () => ({ mcp_fulfillments: {} }),
    oauth: async () => ({ oauth_fulfillments: {} }),
    settings: async () => ({ values: {} }),
    secrets: async () => ({ secret_fulfillments: {} }),
    form: async () => ({ form_fulfillments: {} }),
    oauthRedirectUri: () => null,
  };
}

export async function collectAgentResponse(
  client: Client,
  message: Parameters<Client['sendMessageStream']>[0]['message'],
) {
  const stream = client.sendMessageStream({ message });
  const parts: string[] = [];

  for await (const event of stream) {
    if (event.kind === 'status-update') {
      for (const part of event.status.message?.parts ?? []) {
        if (part.kind === 'text') {
          parts.push(part.text);
        }
      }
    }
  }

  return parts.join('');
}

export async function createA2AClient(url: string) {
  const factory = new ClientFactory(
    ClientFactoryOptions.createFrom(ClientFactoryOptions.default, {
      transports: [new JsonRpcTransportFactory()],
      cardResolver: new DefaultAgentCardResolver(),
    }),
  );

  const client = await factory.createFromUrl(url, '.well-known/agent-card.json');
  const agentCard = await client.getAgentCard();

  const { demands } = handleAgentCard(agentCard);
  const createMessage = buildMessageBuilder(agentCard);

  return {
    client,
    agentCard,
    demands,
    createMessage,
  };
}

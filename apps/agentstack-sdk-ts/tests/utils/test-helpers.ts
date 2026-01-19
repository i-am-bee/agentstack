/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import {
  ClientFactory,
  ClientFactoryOptions,
  DefaultAgentCardResolver,
  JsonRpcTransportFactory,
} from '@a2a-js/sdk/client';
import net from 'net';

import type { Fulfillments } from '../../src/client/core';
import { buildMessageBuilder, handleAgentCard } from '../../src/client/core';
import { type ServerHandle } from '../../src/server';

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

export const buildAgentTest =
  (
    agentBuilder: (port: number) => Promise<ServerHandle>,
    test: (client: Awaited<ReturnType<typeof createA2AClient>>) => Promise<void>,
  ) =>
  async () => {
    const port = await getRandomPort();
    const serverHandle = await agentBuilder(port);
    const client = await createA2AClient(serverHandle.url);

    try {
      await test(client);
    } finally {
      await serverHandle.close();
    }
  };

export const accumulateResponse = async (
  stream: ReturnType<Awaited<ReturnType<typeof createA2AClient>>['client']['sendMessageStream']>,
) => {
  let responseText = '';
  for await (const event of stream) {
    if (event.kind === 'status-update') {
      const textPart = event.status.message?.parts?.find((p) => p.kind === 'text');
      if (textPart && 'text' in textPart) {
        responseText = textPart.text;
      }
    }
  }

  return responseText;
};

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

import { buildMessageBuilder, handleAgentCard } from '../src/client/core';

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

export async function createA2AClient(baseUrl: string) {
  const agentCardPath = '.well-known/agent-card.json';
  const factory = new ClientFactory(
    ClientFactoryOptions.createFrom(ClientFactoryOptions.default, {
      transports: [new JsonRpcTransportFactory()],
      cardResolver: new DefaultAgentCardResolver(),
    }),
  );
  const client = await factory.createFromUrl(baseUrl, agentCardPath);
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

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Client } from '@a2a-js/sdk/client';
import { randomUUID } from 'crypto';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';

import type { AgentCard } from '../../src/client/a2a';
import type { ServerHandle } from '../../src/server';
import {
  collectAgentResponse,
  createA2AClient,
  createEchoAgent,
  createTestFulfillments,
  getRandomPort,
} from '../utils/test-helpers';

describe('Echo Agent E2E', () => {
  let serverHandle: ServerHandle;
  let client: Client;
  let agentCard: AgentCard;
  let createMessage: Awaited<ReturnType<typeof createA2AClient>>['createMessage'];

  beforeAll(async () => {
    const port = await getRandomPort();
    serverHandle = await createEchoAgent(port);
    const result = await createA2AClient(serverHandle.url);
    client = result.client;
    agentCard = result.agentCard;
    createMessage = result.createMessage;
  });

  afterAll(async () => {
    await serverHandle.close();
  });

  it('should echo the message back', async () => {
    const testMessage = 'Hello, Agent!';
    const fulfillments = createTestFulfillments();

    const message = await createMessage(randomUUID(), fulfillments, {
      messageId: randomUUID(),
      parts: [{ kind: 'text', text: testMessage }],
    });

    const response = await collectAgentResponse(client, message);

    expect(response).toBe(`Echo: ${testMessage}`);
  });
});

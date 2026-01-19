/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { randomUUID } from 'crypto';
import { describe, expect, it } from 'vitest';

import { accumulateResponse, buildAgentTest, createTestFulfillments } from '../utils/test-helpers';
import { ServerHandle } from '../../src/experimental/server/types';
import { Server } from '../../src/server';
import { Part } from '@a2a-js/sdk';

async function createEchoAgent(port: number): Promise<ServerHandle> {
  const server = new Server();

  return server
    .agent({
      name: 'EchoAgent',
      description: 'An echo agent for testing',
      version: '1.0.0',
      handler: async function* (input) {
        const firstPart = input.parts?.[0] as Part | undefined;
        if (firstPart?.kind === 'text') {
          yield `Echo: ${firstPart.text}`;
        } else {
          yield 'No text part found';
        }
      },
    })
    .run({ port, host: '127.0.0.1' });
}

describe('Echo Agent E2E', () => {
  it(
    'should echo the message back',
    buildAgentTest(createEchoAgent, async ({ createMessage, client }) => {
      const testMessage = 'Hello, Agent!';
      const contextId = randomUUID();
      const fulfillments = createTestFulfillments();

      const message = await createMessage(contextId, fulfillments, {
        messageId: randomUUID(),
        parts: [{ kind: 'text', text: testMessage }],
      });

      const stream = client.sendMessageStream({ message });
      const responseText = await accumulateResponse(stream);
      expect(responseText).toBe(`Echo: ${testMessage}`);
    }),
  );
});

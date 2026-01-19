/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { randomUUID } from 'crypto';
import { describe, expect, it } from 'vitest';

import { accumulateResponse, buildAgentTest, createEchoAgent, createTestFulfillments } from '../utils/test-helpers';

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

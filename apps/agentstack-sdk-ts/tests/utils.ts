/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Fulfillments } from '../src/client/core';
import { isTextPart } from '../src/experimental/server/a2a/utils';
import type { ServerHandle } from '../src/experimental/server/core';
import { createA2AClient, getRandomPort } from './helpers';

export type Client = Awaited<ReturnType<typeof createA2AClient>>;

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

export function buildAgentTest(
  agentBuilder: (port: number) => Promise<ServerHandle>,
  test: (client: Client) => Promise<void>,
) {
  return async function () {
    const port = await getRandomPort();
    const serverHandle = await agentBuilder(port);
    const client = await createA2AClient(serverHandle.url);

    try {
      await test(client);
    } finally {
      await serverHandle.close();
    }
  };
}

export async function accumulateResponse(stream: ReturnType<Client['client']['sendMessageStream']>) {
  let responseText = '';

  for await (const event of stream) {
    if (event.kind === 'status-update') {
      const textPart = event.status.message?.parts.find(isTextPart);

      if (textPart) {
        responseText = textPart.text;
      }
    }
  }

  return responseText;
}

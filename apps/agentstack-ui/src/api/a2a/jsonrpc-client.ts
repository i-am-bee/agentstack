/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { AgentCard, Message, StreamResponse, Task } from 'agentstack-sdk';
import { agentCardSchema, streamResponseSchema } from 'agentstack-sdk';
import { EventSourceParserStream } from 'eventsource-parser/stream';
import { v4 as uuid } from 'uuid';

export interface A2AClient {
  getAgentCard(): Promise<AgentCard>;
  sendMessageStream(params: {
    message: Message;
    configuration?: Record<string, unknown>;
    metadata?: Record<string, unknown>;
  }): AsyncIterable<StreamResponse>;
  getTask(params: { id: string }): Promise<Task>;
  cancelTask(params: { id: string }): Promise<Task>;
}

interface CreateClientParams {
  endpointUrl: string;
  agentCard: AgentCard;
  fetchImpl: typeof fetch;
}

export function createA2AClient({ endpointUrl, agentCard, fetchImpl }: CreateClientParams): A2AClient {
  async function jsonRpcRequest(method: string, params: Record<string, unknown>) {
    const response = await fetchImpl(endpointUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        jsonrpc: '2.0',
        id: uuid(),
        method,
        params,
      }),
    });

    if (!response.ok) {
      throw new Error(`A2A request failed: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();

    if (data.error) {
      const err = new Error(data.error.message ?? 'A2A error');
      Object.assign(err, { code: data.error.code, data: data.error.data });
      throw err;
    }

    return data.result;
  }

  return {
    getAgentCard: async () => agentCard,

    async *sendMessageStream(params) {
      const response = await fetchImpl(endpointUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          jsonrpc: '2.0',
          id: uuid(),
          method: 'SendStreamingMessage',
          params,
        }),
      });

      if (!response.ok) {
        throw new Error(`A2A stream request failed: ${response.status} ${response.statusText}`);
      }

      if (!response.body) {
        throw new Error('Response body is empty');
      }

      const eventStream = response.body.pipeThrough(new TextDecoderStream()).pipeThrough(new EventSourceParserStream());
      const reader = eventStream.getReader();

      try {
        while (true) {
          const { done, value: event } = await reader.read();
          if (done) break;

          if (!event.event || event.event === 'message') {
            const data = JSON.parse(event.data);

            if (data.error) {
              const err = new Error(data.error.message ?? 'A2A streaming error');
              Object.assign(err, { code: data.error.code, data: data.error.data });
              throw err;
            }

            if (data.result) {
              const parsed = streamResponseSchema.parse(data.result);
              yield parsed;
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    },

    async getTask(params) {
      return jsonRpcRequest('GetTask', params) as Promise<Task>;
    },

    async cancelTask(params) {
      return jsonRpcRequest('CancelTask', params) as Promise<Task>;
    },
  };
}

export async function fetchAgentCard(url: string, fetchImpl: typeof fetch): Promise<AgentCard> {
  const response = await fetchImpl(url);

  if (!response.ok) {
    throw new Error(`Failed to fetch agent card: ${response.status} ${response.statusText}`);
  }

  const data = await response.json();
  return agentCardSchema.parse(data);
}

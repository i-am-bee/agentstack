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
import { type ContextToken, createAuthenticatedFetch, getAgentCardPath } from 'agentstack-sdk';
import { useEffect, useState } from 'react';

import { createContext, createContextToken } from './api';
import { BASE_URL, PROVIDER_ID } from './constants';
import type { Session } from './types';
import { extractTextFromMessage, resolveAgentMetadata } from './utils';

async function ensureSession() {
  if (!BASE_URL || !PROVIDER_ID) {
    throw new Error(`Missing required environment variables.`);
  }

  const context = await createContext();
  const contextToken = await createContextToken(context.id);
  const client = await createClient(contextToken);
  const metadata = await resolveAgentMetadata({ client, contextToken });

  return {
    client,
    contextId: context.id,
    metadata,
  };
}

async function createClient(contextToken: ContextToken) {
  const fetchImpl = createAuthenticatedFetch(contextToken.token);

  const factory = new ClientFactory(
    ClientFactoryOptions.createFrom(ClientFactoryOptions.default, {
      transports: [new JsonRpcTransportFactory({ fetchImpl })],
      cardResolver: new DefaultAgentCardResolver({ fetchImpl }),
    }),
  );

  const agentCardPath = getAgentCardPath(PROVIDER_ID);
  const client = await factory.createFromUrl(BASE_URL, agentCardPath);

  return client;
}

export function useAgent() {
  const [session, setSession] = useState<Session>();
  const [isInitializing, setIsInitializing] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (session) {
      return;
    }

    let cancelled = false;

    (async () => {
      try {
        setIsInitializing(true);

        const session = await ensureSession();

        if (cancelled) {
          return;
        }

        setSession(session);
      } catch (error) {
        if (cancelled) {
          return;
        }

        const message = error instanceof Error ? error.message : 'Failed to connect to agent.';

        setError(message);
      } finally {
        if (!cancelled) {
          setIsInitializing(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [session]);

  const sendMessage = async ({ text }: { text: string }) => {
    if (!session) {
      throw new Error('Agent is not ready yet.');
    }

    const { client, contextId, metadata } = session;

    const runStream = async () => {
      const stream = client.sendMessageStream({
        message: {
          kind: 'message',
          role: 'user',
          messageId: crypto.randomUUID(),
          contextId,
          parts: [{ kind: 'text', text }],
          metadata,
        },
      });

      let agentText = '';

      for await (const event of stream) {
        if (event.kind === 'status-update' || event.kind === 'message') {
          const message = event.kind === 'message' ? event : event.status.message;
          const text = extractTextFromMessage(message);

          if (text) {
            agentText += text;
          }
        }
      }

      return {
        text: agentText,
      };
    };

    return await runStream();
  };

  return {
    session,
    isInitializing,
    error,
    sendMessage,
  };
}

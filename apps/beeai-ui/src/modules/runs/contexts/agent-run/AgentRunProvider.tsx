/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';
import { type PropsWithChildren, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { v4 as uuid } from 'uuid';

import { buildA2AClient } from '#api/a2a/client.ts';
import type { ChatRun } from '#api/a2a/types.ts';
import { createTextPart } from '#api/a2a/utils.ts';
import { getErrorCode } from '#api/utils.ts';
import { useHandleError } from '#hooks/useHandleError.ts';
import { useImmerWithGetter } from '#hooks/useImmerWithGetter.ts';
import type { Agent } from '#modules/agents/api/types.ts';
import { FileUploadProvider } from '#modules/files/contexts/FileUploadProvider.tsx';
import { useFileUpload } from '#modules/files/contexts/index.ts';
import { convertFilesToUIFileParts } from '#modules/files/utils.ts';
import { Role } from '#modules/messages/api/types.ts';
import type { UIAgentMessage, UIMessage, UIUserMessage } from '#modules/messages/types.ts';
import { UIMessageStatus } from '#modules/messages/types.ts';
import { addTranformedMessagePart, isAgentMessage } from '#modules/messages/utils.ts';
import type { RunStats } from '#modules/runs/types.ts';
import { SourcesProvider } from '#modules/sources/contexts/SourcesProvider.tsx';
import { getMessageSourcesMap } from '#modules/sources/utils.ts';

import { MessagesProvider } from '../../../messages/contexts/MessagesProvider';
import { AgentStatusProvider } from '../agent-status/AgentStatusProvider';
import { AgentRunContext } from './agent-run-context';

interface Props {
  agent: Agent;
}

export function AgentRunProviders({ agent, children }: PropsWithChildren<Props>) {
  return (
    <FileUploadProvider allowedContentTypes={agent.defaultInputModes}>
      <AgentRunProvider agent={agent}>{children}</AgentRunProvider>
    </FileUploadProvider>
  );
}

function AgentRunProvider({ agent, children }: PropsWithChildren<Props>) {
  const [contextId, setContextId] = useState<string | null>(null);
  const [messages, getMessages, setMessages] = useImmerWithGetter<UIMessage[]>([]);
  const [input, setInput] = useState<string>();
  const [isPending, setIsPending] = useState(false);
  const [stats, setStats] = useState<RunStats>();

  const pendingSubscription = useRef<() => void>(undefined);
  const pendingRun = useRef<ChatRun>(undefined);

  const errorHandler = useHandleError();

  useEffect(() => {
    (async () => {
      const context = await fetch('/api/v1/contexts', { method: 'POST' });
      const contextData = await context.json();
      setContextId(contextData.id as string);
    })();
  }, [setContextId]);

  const a2aAgentClient = useMemo(
    () => buildA2AClient({ providerId: agent.provider.id, extensions: agent.capabilities.extensions ?? [] }),
    [agent.provider.id, agent.capabilities.extensions],
  );
  const { files, clearFiles } = useFileUpload();

  const updateLastAgentMessage = useCallback(
    (updater: (message: UIAgentMessage) => void) => {
      setMessages((messages) => {
        const lastMessage = messages.at(-1);

        if (lastMessage && isAgentMessage(lastMessage)) {
          updater(lastMessage);
        } else {
          throw new Error('There is no last agent message.');
        }
      });
    },
    [setMessages],
  );

  const handleError = useCallback(
    (error: unknown) => {
      const errorCode = getErrorCode(error);

      errorHandler(error, {
        errorToast: { title: errorCode?.toString() ?? 'Failed to run agent.', includeErrorMessage: true },
      });

      if (error instanceof Error) {
        updateLastAgentMessage((message) => {
          message.error = error;
          message.status = UIMessageStatus.Failed;
        });
      }
    },
    [errorHandler, updateLastAgentMessage],
  );

  const cancel = useCallback(async () => {
    if (pendingRun.current && pendingSubscription.current) {
      updateLastAgentMessage((message) => {
        message.status = UIMessageStatus.Aborted;
      });

      pendingSubscription.current();
      await pendingRun.current.cancel();
    } else {
      throw new Error('No run in progress');
    }
  }, [updateLastAgentMessage]);

  const clear = useCallback(() => {
    setMessages([]);
    setStats(undefined);
    clearFiles();
    setContextId(uuid());
    setIsPending(false);
    setInput(undefined);
    pendingRun.current = undefined;
  }, [setMessages, clearFiles, setContextId]);

  const run = useCallback(
    async (input: string) => {
      if (contextId === null) {
        throw new Error('Context ID is not set');
      }

      if (pendingRun.current || pendingSubscription.current) {
        throw new Error('A run is already in progress');
      }

      setInput(input);
      setIsPending(true);
      setStats({ startTime: Date.now() });

      const token = await fetch(`/api/v1/contexts/${contextId}/token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          grant_global_permissions: {
            llm: ['*'],
          },
          grant_context_permissions: {
            llm: ['*'],
          },
        }),
      });
      const tokenData = await token.json();

      const userMessage: UIUserMessage = {
        id: uuid(),
        role: Role.User,
        parts: [createTextPart(input), ...convertFilesToUIFileParts(files)],
      };
      const agentMessage: UIAgentMessage = {
        id: uuid(),
        role: Role.Agent,
        parts: [],
        status: UIMessageStatus.InProgress,
      };

      setMessages((messages) => {
        messages.push(userMessage, agentMessage);
      });

      clearFiles();

      try {
        const run = a2aAgentClient.chat({
          message: userMessage,
          contextId,
          fulfillments: {
            mcp: async () => {
              throw new Error('MCP fulfillment not implemented');
            },
            llm: async () => {
              return {
                llm_fulfillments: {
                  default: {
                    identifier: 'llm_proxy',
                    api_base: '{platform_url}/api/v1/llm/',
                    api_key: tokenData.token,
                    api_model: 'dummy',
                  },
                },
              };
            },
          },
        });
        pendingRun.current = run;

        pendingSubscription.current = run.subscribe(({ parts, taskId }) => {
          updateLastAgentMessage((message) => {
            message.id = taskId;
          });

          parts.forEach((part) => {
            updateLastAgentMessage((message) => {
              const updatedParts = addTranformedMessagePart(part, message);
              message.parts = updatedParts;
            });
          });
        });

        await run.done;

        updateLastAgentMessage((message) => {
          message.status = UIMessageStatus.Completed;
        });
      } catch (error) {
        handleError(error);
      } finally {
        setIsPending(false);
        setStats((stats) => ({ ...stats, endTime: Date.now() }));
        pendingRun.current = undefined;
        pendingSubscription.current = undefined;
      }
    },
    [a2aAgentClient, files, contextId, handleError, updateLastAgentMessage, setMessages, clearFiles],
  );

  const sources = useMemo(() => getMessageSourcesMap(messages), [messages]);

  const contextValue = useMemo(() => {
    if (contextId === null) {
      return null;
    }

    return {
      agent,
      isPending,
      input,
      stats,
      contextId,
      run,
      cancel,
      clear,
    };
  }, [agent, isPending, input, stats, contextId, run, cancel, clear]);

  return (
    <AgentStatusProvider agent={agent} isMonitorStatusEnabled>
      <SourcesProvider sources={sources}>
        <MessagesProvider messages={getMessages()}>
          {contextValue && <AgentRunContext.Provider value={contextValue}>{children}</AgentRunContext.Provider>}
        </MessagesProvider>
      </SourcesProvider>
    </AgentStatusProvider>
  );
}

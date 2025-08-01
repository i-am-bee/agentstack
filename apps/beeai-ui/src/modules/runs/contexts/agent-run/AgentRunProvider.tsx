/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { type PropsWithChildren, useCallback, useMemo, useRef, useState } from 'react';
import { match } from 'ts-pattern';
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
import { convertFilesToUIFileParts, transformFilePart } from '#modules/files/utils.ts';
import { Role } from '#modules/messages/api/types.ts';
import type { UIAgentMessage, UIMessage, UIUserMessage } from '#modules/messages/types.ts';
import { UIMessagePartKind, UIMessageStatus } from '#modules/messages/types.ts';
import { isAgentMessage, sortMessageParts } from '#modules/messages/utils.ts';
import type { RunStats } from '#modules/runs/types.ts';
import { SourcesProvider } from '#modules/sources/contexts/SourcesProvider.tsx';
import { getMessageSourcesMap, transformSourcePart } from '#modules/sources/utils.ts';

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
  const [conversationId, setConversationId] = useState<string>(uuid());
  const [messages, getMessages, setMessages] = useImmerWithGetter<UIMessage[]>([]);
  const [input, setInput] = useState<string>();
  const [isPending, setIsPending] = useState(false);
  const [stats, setStats] = useState<RunStats>();

  const pendingSubscription = useRef<() => void>(undefined);
  const pendingRun = useRef<ChatRun>(undefined);

  const errorHandler = useHandleError();

  const a2aAgentClient = useMemo(() => buildA2AClient(agent.provider.id), [agent.provider.id]);
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
    setConversationId(uuid());
    setIsPending(false);
    setInput(undefined);
    pendingRun.current = undefined;
  }, [setMessages, clearFiles, setConversationId]);

  const run = useCallback(
    async (input: string) => {
      if (pendingRun.current || pendingSubscription.current) {
        throw new Error('A run is already in progress');
      }

      setInput(input);
      setIsPending(true);
      setStats({ startTime: Date.now() });

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
          contextId: conversationId,
        });
        pendingRun.current = run;

        pendingSubscription.current = run.subscribe(({ parts, taskId }) => {
          updateLastAgentMessage((message) => {
            message.id = taskId;
          });

          parts.forEach((part) => {
            updateLastAgentMessage((message) => {
              match(part)
                .with({ kind: UIMessagePartKind.File }, (part) => {
                  const transformedPart = transformFilePart(part, message);

                  if (transformedPart) {
                    message.parts.push(transformedPart);
                  } else {
                    message.parts.push(part);
                  }
                })
                .with({ kind: UIMessagePartKind.Source }, (part) => {
                  const transformedPart = transformSourcePart(part);

                  message.parts.push(part, transformedPart);
                })
                .otherwise((part) => {
                  message.parts.push(part);
                });

              message.parts = sortMessageParts(message.parts);
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
    [a2aAgentClient, files, conversationId, handleError, updateLastAgentMessage, setMessages, clearFiles],
  );

  const sources = useMemo(() => getMessageSourcesMap(messages), [messages]);

  const contextValue = useMemo(
    () => ({
      agent,
      isPending,
      input,
      stats,
      run,
      cancel,
      clear,
    }),
    [agent, isPending, input, stats, run, cancel, clear],
  );

  return (
    <AgentStatusProvider agent={agent} isMonitorStatusEnabled>
      <SourcesProvider sources={sources}>
        <MessagesProvider messages={getMessages()}>
          <AgentRunContext.Provider value={contextValue}>{children}</AgentRunContext.Provider>
        </MessagesProvider>
      </SourcesProvider>
    </AgentStatusProvider>
  );
}

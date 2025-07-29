/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { type PropsWithChildren, useCallback, useMemo, useRef, useState } from 'react';
import { match } from 'ts-pattern';
import { v4 as uuid } from 'uuid';

import type { ChatRun } from '#api/a2a/a2aClient.ts';
import { buildA2AClient } from '#api/a2a/a2aClient.ts';
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
  const [input, setInput] = useState<string | undefined>(undefined);
  const [isPending, setIsPending] = useState(false);
  const [stats, setStats] = useState<RunStats>();

  const pendingSubscription = useRef<(() => void) | undefined>(undefined);
  const pendingRun = useRef<ChatRun | undefined>(undefined);

  const errorHandler = useHandleError();

  const a2aAgentClient = useMemo(() => buildA2AClient(agent.url), [agent.url]);
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
      pendingSubscription.current();
      await pendingRun.current.cancel();
    } else {
      throw new Error('No run in progress');
    }
  }, []);

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

      try {
        setMessages((messages) => {
          const userMessage: UIUserMessage = {
            id: uuid(),
            role: Role.User,
            parts: [{ kind: UIMessagePartKind.Text, id: uuid(), text: input }, ...convertFilesToUIFileParts(files)],
          };
          const agentMessage: UIAgentMessage = {
            id: uuid(),
            role: Role.Agent,
            parts: [],
            status: UIMessageStatus.InProgress,
          };

          messages.push(...[userMessage, agentMessage]);
        });

        const run = a2aAgentClient.chat(input, files, conversationId);
        pendingRun.current = run;

        pendingSubscription.current = run.subscribe((parts) => {
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

        updateLastAgentMessage((message) => {
          message.error = error;
          message.status = UIMessageStatus.Failed;
        });
      } finally {
        setIsPending(false);
        setStats((stats) => ({ ...stats, endTime: Date.now() }));
        pendingRun.current = undefined;
        pendingSubscription.current = undefined;
      }
    },
    [handleError, updateLastAgentMessage, files, conversationId, setMessages],
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

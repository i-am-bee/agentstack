/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';
import { type PropsWithChildren, useCallback, useMemo, useRef, useState } from 'react';
import { v4 as uuid } from 'uuid';

import { buildA2AClient } from '#api/a2a/client.ts';
import type { AgentA2AClient, ChatRun } from '#api/a2a/types.ts';
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
import { usePlatformContext } from '#modules/platform-context/contexts/index.ts';
import { PlatformContextProvider } from '#modules/platform-context/contexts/PlatformContextProvider.tsx';
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
  const agentClient = useMemo(
    () =>
      buildA2AClient({
        providerId: agent.provider.id,
        extensions: agent.capabilities.extensions ?? [],
      }),
    [agent.provider.id, agent.capabilities.extensions],
  );

  return (
    <PlatformContextProvider agentClient={agentClient}>
      <FileUploadProvider allowedContentTypes={agent.defaultInputModes}>
        <AgentRunProvider agent={agent} agentClient={agentClient}>
          {children}
        </AgentRunProvider>
      </FileUploadProvider>
    </PlatformContextProvider>
  );
}

interface AgentRunProviderProps extends Props {
  agentClient: AgentA2AClient;
}

function AgentRunProvider({ agent, agentClient, children }: PropsWithChildren<AgentRunProviderProps>) {
  const { getContextId, resetContext, getFullfilments } = usePlatformContext();
  const [messages, getMessages, setMessages] = useImmerWithGetter<UIMessage[]>([]);
  const [input, setInput] = useState<string>();
  const [isPending, setIsPending] = useState(false);
  const [stats, setStats] = useState<RunStats>();

  const pendingSubscription = useRef<() => void>(undefined);
  const pendingRun = useRef<ChatRun>(undefined);

  const errorHandler = useHandleError();

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
    resetContext();
    setIsPending(false);
    setInput(undefined);
    pendingRun.current = undefined;
  }, [setMessages, clearFiles, resetContext]);

  const run = useCallback(
    async (input: string) => {
      const contextId = getContextId();

      if (pendingRun.current || pendingSubscription.current) {
        throw new Error('A run is already in progress');
      }

      setInput(input);
      setIsPending(true);
      setStats({ startTime: Date.now() });

      const fulfillments = await getFullfilments();

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
        const run = agentClient.chat({
          message: userMessage,
          contextId,
          fulfillments,
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
    [getContextId, getFullfilments, files, setMessages, clearFiles, agentClient, updateLastAgentMessage, handleError],
  );

  const sources = useMemo(() => getMessageSourcesMap(messages), [messages]);

  const contextValue = useMemo(() => {
    return {
      agent,
      isPending,
      input,
      stats,
      run,
      cancel,
      clear,
    };
  }, [agent, isPending, input, stats, run, cancel, clear]);

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

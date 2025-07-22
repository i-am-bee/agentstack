/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import type { FilePart, TextPart } from '@a2a-js/sdk';
import type { MessagePart } from 'acp-sdk';
import { type PropsWithChildren, useCallback, useMemo, useState } from 'react';
import { v4 as uuid } from 'uuid';

import { getErrorCode } from '#api/utils.ts';
import { useHandleError } from '#hooks/useHandleError.ts';
import { useImmerWithGetter } from '#hooks/useImmerWithGetter.ts';
import type { Agent } from '#modules/agents/api/types.ts';
import { FileUploadProvider } from '#modules/files/contexts/FileUploadProvider.tsx';
import { useFileUpload } from '#modules/files/contexts/index.ts';
import { convertFilesToUIFileParts, processFilePart } from '#modules/files/utils.ts';
import { Role } from '#modules/messages/api/types.ts';
import type { UIAgentMessage, UIMessage, UIMessagePart, UIUserMessage } from '#modules/messages/types.ts';
import { UIMessagePartKind, UIMessageStatus } from '#modules/messages/types.ts';
import { convertUIMessageParts, isAgentMessage, processTextPart, sortMessageParts } from '#modules/messages/utils.ts';
import { useRunAgent } from '#modules/runs/hooks/useRunAgent.ts';
import type { RunStats } from '#modules/runs/types.ts';
import { SourcesProvider } from '#modules/sources/contexts/SourcesProvider.tsx';
import { getMessageSourcesMap, processSourcePart } from '#modules/sources/utils.ts';
import { processTrajectoryPart } from '#modules/trajectories/utils.ts';

import { MessagesProvider } from '../../../messages/contexts/MessagesProvider';
import { AgentClientProvider } from '../agent-client/AgentClientProvider';
import { AgentStatusProvider } from '../agent-status/AgentStatusProvider';
import { AgentRunContext } from './agent-run-context';

type MessagePartMetadata = NonNullable<MessagePart['metadata']>;

interface Props {
  agent: Agent;
}

export function AgentRunProviders({ agent, children }: PropsWithChildren<Props>) {
  return (
    <FileUploadProvider allowedContentTypes={agent.defaultInputModes}>
      <AgentClientProvider agent={agent}>
        <AgentRunProvider agent={agent}>{children}</AgentRunProvider>
      </AgentClientProvider>
    </FileUploadProvider>
  );
}

function AgentRunProvider({ agent, children }: PropsWithChildren<Props>) {
  const [messages, getMessages, setMessages] = useImmerWithGetter<UIMessage[]>([]);
  const [stats, setStats] = useState<RunStats>();

  const errorHandler = useHandleError();

  const { files, clearFiles } = useFileUpload();
  const { input, isPending, runAgent, stopAgent, reset } = useRunAgent({
    onStart: () => {
      setStats({ startTime: Date.now() });
    },
    onStop: () => {
      updateLastAgentMessage((message) => {
        message.status = UIMessageStatus.Aborted;
      });
    },
    onDone: () => {
      setStats((stats) => ({ ...stats, endTime: Date.now() }));
    },
    onPart: (event) => {
      switch (event.kind) {
        case 'text':
          handleTextPart(event);

          break;
        case 'file':
          handleFilePart(event);

          break;
      }

      const { metadata } = event;

      if (metadata) {
        processMetadata(metadata as MessagePartMetadata);
      }

      updateLastAgentMessage((message) => {
        message.parts = sortMessageParts(message.parts);
      });
    },
    onCompleted: () => {
      updateLastAgentMessage((message) => {
        message.status = UIMessageStatus.Completed;
      });
    },
    onFailed: (_, error) => {
      handleError(error);

      updateLastAgentMessage((message) => {
        message.error = error;
        message.status = UIMessageStatus.Failed;
      });
    },
  });

  const updateLastAgentMessage = useCallback(
    (updater: (message: UIAgentMessage) => void) => {
      setMessages((messages) => {
        const lastMessage = messages.at(-1);

        if (lastMessage && isAgentMessage(lastMessage)) {
          updater(lastMessage);
        }
      });
    },
    [setMessages],
  );

  const processMetadata = useCallback(
    (metadata: MessagePartMetadata) => {
      switch (metadata.kind) {
        case 'citation':
          updateLastAgentMessage((message) => {
            message.parts.push(...processSourcePart(metadata, message));
          });

          break;
        case 'trajectory':
          updateLastAgentMessage((message) => {
            message.parts.push(processTrajectoryPart(metadata));
          });

          break;
      }
    },
    [updateLastAgentMessage],
  );

  const handleTextPart = useCallback(
    (part: TextPart) => {
      updateLastAgentMessage((message) => {
        message.parts.push(processTextPart(part));
      });
    },
    [updateLastAgentMessage],
  );

  const handleFilePart = useCallback(
    (part: FilePart) => {
      updateLastAgentMessage((message) => {
        message.parts.push(...processFilePart(part, message));
      });
    },
    [updateLastAgentMessage],
  );

  const handleError = useCallback(
    (error: unknown) => {
      const errorCode = getErrorCode(error);

      errorHandler(error, {
        errorToast: { title: errorCode?.toString() ?? 'Failed to run agent.', includeErrorMessage: true },
      });
    },
    [errorHandler],
  );

  const cancel = useCallback(() => {
    stopAgent();
  }, [stopAgent]);

  const clear = useCallback(() => {
    reset();
    setMessages([]);
    setStats(undefined);
    clearFiles();
  }, [reset, setMessages, clearFiles]);

  const run = useCallback(
    async (input: string) => {
      const parts: UIMessagePart[] = [
        {
          id: uuid(),
          kind: UIMessagePartKind.Text,
          text: input,
        },
        ...convertFilesToUIFileParts(files),
      ];

      setMessages((messages) => {
        const userMessage: UIUserMessage = {
          id: uuid(),
          role: Role.User,
          parts,
        };
        const agentMessage: UIAgentMessage = {
          id: uuid(),
          role: Role.Agent,
          parts: [],
          status: UIMessageStatus.InProgress,
        };

        messages.push(...[userMessage, agentMessage]);
      });

      clearFiles();

      try {
        await runAgent({ agent, parts: convertUIMessageParts(parts) });
      } catch (error) {
        handleError(error);
      }
    },
    [agent, files, setMessages, clearFiles, runAgent, handleError],
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

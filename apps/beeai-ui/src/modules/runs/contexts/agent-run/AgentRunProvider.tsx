/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import type { FilePart, Part, TextPart } from '@a2a-js/sdk';
import { type PropsWithChildren, useCallback, useMemo, useState } from 'react';
import { v4 as uuid } from 'uuid';

import { getErrorCode } from '#api/utils.ts';
import { useHandleError } from '#hooks/useHandleError.ts';
import { useImmerWithGetter } from '#hooks/useImmerWithGetter.ts';
import type { Agent } from '#modules/agents/api/types.ts';
import type { MessagePart } from '#modules/runs/api/types.ts';
import {
  type AgentMessage,
  type ChatMessage,
  type CitationTransform,
  MessageContentTransformType,
  MessageStatus,
} from '#modules/runs/chat/types.ts';
import { FileUploadProvider } from '#modules/runs/files/contexts/FileUploadProvider.tsx';
import { getFileUri, prepareMessageFiles } from '#modules/runs/files/utils.ts';
import { useRunAgent } from '#modules/runs/hooks/useRunAgent.ts';
import { SourcesProvider } from '#modules/runs/sources/contexts/SourcesProvider.tsx';
import { extractSources, prepareMessageSources } from '#modules/runs/sources/utils.ts';
import { prepareTrajectories } from '#modules/runs/trajectory/utils.ts';
import { Role, type RunStats } from '#modules/runs/types.ts';
import {
  applyContentTransforms,
  createCitationTransform,
  createFileParts,
  createImageTransform,
  extractValidUploadFiles,
  isAgentMessage,
  mapToMessageFiles,
} from '#modules/runs/utils.ts';
import { isImageMimeType } from '#utils/helpers.ts';

import { useFileUpload } from '../../files/contexts';
import { AgentClientProvider } from '../agent-client/AgentClientProvider';
import { AgentStatusProvider } from '../agent-status/AgentStatusProvider';
import { MessagesProvider } from '../messages/MessagesProvider';
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
  const [messages, getMessages, setMessages] = useImmerWithGetter<ChatMessage[]>([]);
  const [stats, setStats] = useState<RunStats>();

  const errorHandler = useHandleError();

  const { files, clearFiles } = useFileUpload();
  const { input, isPending, runAgent, stopAgent, reset } = useRunAgent({
    onStart: () => {
      setStats({ startTime: Date.now() });
    },
    onStop: () => {
      updateLastAgentMessage((message) => {
        message.status = MessageStatus.Aborted;
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
        message.content = applyContentTransforms({
          rawContent: message.rawContent,
          transforms: message.contentTransforms,
        });
      });
    },
    onCompleted: () => {
      updateLastAgentMessage((message) => {
        message.status = MessageStatus.Completed;
      });
    },
    onFailed: (_, error) => {
      handleError(error);

      updateLastAgentMessage((message) => {
        message.error = error;
        message.status = MessageStatus.Failed;
      });
    },
  });

  const updateLastAgentMessage = useCallback(
    (updater: (message: AgentMessage) => void) => {
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
            const { sources, newSource } = prepareMessageSources({ message, metadata });

            message.sources = sources;

            if (newSource == null) {
              return;
            }

            const citationTransformGroup = message.contentTransforms.find(
              (transform): transform is CitationTransform =>
                transform.kind === MessageContentTransformType.Citation &&
                transform.startIndex === newSource.startIndex,
            );

            if (citationTransformGroup) {
              citationTransformGroup.sources.push(newSource);
            } else {
              message.contentTransforms.push(createCitationTransform({ source: newSource }));
            }
          });

          break;
        case 'trajectory':
          updateLastAgentMessage((message) => {
            message.trajectories = prepareTrajectories({ trajectories: message.trajectories, data: metadata });
          });

          break;
      }
    },
    [updateLastAgentMessage],
  );

  const handleTextPart = useCallback(
    (part: TextPart) => {
      const { text } = part;

      updateLastAgentMessage((message) => {
        message.rawContent += text;
      });
    },
    [updateLastAgentMessage],
  );

  const handleFilePart = useCallback(
    (event: FilePart) => {
      const { file } = event;
      const { mimeType } = file;

      const isImage = isImageMimeType(mimeType);

      if (isImage) {
        updateLastAgentMessage((message) => {
          message.contentTransforms.push(
            createImageTransform({
              imageUrl: getFileUri(file),
              insertAt: message.rawContent.length,
            }),
          );
        });
      } else {
        updateLastAgentMessage((message) => {
          message.files = prepareMessageFiles({ files: message.files, file });
        });
      }
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
      const uploadFiles = extractValidUploadFiles(files);
      const parts: Part[] = [{ kind: 'text', text: input }, ...createFileParts(uploadFiles)];
      const userFiles = mapToMessageFiles(uploadFiles);

      setMessages((messages) => {
        messages.push({
          key: uuid(),
          role: Role.User,
          content: input,
          files: userFiles,
        });
        messages.push({
          key: uuid(),
          role: Role.Agent,
          content: '',
          rawContent: '',
          contentTransforms: [],
          status: MessageStatus.InProgress,
        });
      });

      clearFiles();

      try {
        await runAgent({ agent, parts });
      } catch (error) {
        handleError(error);
      }
    },
    [agent, files, setMessages, clearFiles, runAgent, handleError],
  );

  const sourcesData = useMemo(() => extractSources(messages), [messages]);

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
      <SourcesProvider sourcesData={sourcesData}>
        <MessagesProvider messages={getMessages()}>
          <AgentRunContext.Provider value={contextValue}>{children}</AgentRunContext.Provider>
        </MessagesProvider>
      </SourcesProvider>
    </AgentStatusProvider>
  );
}

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import isString from 'lodash/isString';
import type { PropsWithChildren } from 'react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { v4 as uuid } from 'uuid';

import { getErrorCode } from '#api/utils.ts';
import { useHandleError } from '#hooks/useHandleError.ts';
import { usePrevious } from '#hooks/usePrevious.ts';
import type { Agent } from '#modules/agents/api/types.ts';
import type { MessagePartMetadata } from '#modules/runs/api/types.ts';
import {
  type AgentMessage,
  type CitationTransform,
  MessageContentTransformType,
  MessageStatus,
} from '#modules/runs/chat/types.ts';
import { prepareMessageFiles } from '#modules/runs/files/utils.ts';
import { useRunAgent } from '#modules/runs/hooks/useRunAgent.ts';
import { SourcesProvider } from '#modules/runs/sources/contexts/SourcesProvider.tsx';
import { extractSources, prepareMessageSources } from '#modules/runs/sources/utils.ts';
import { prepareTrajectories } from '#modules/runs/trajectory/utils.ts';
import { Role, type RunLog, type RunStats } from '#modules/runs/types.ts';
import {
  applyContentTransforms,
  createCitationTransform,
  createFileMessageParts,
  createImageTransform,
  createMessagePart,
  extractValidUploadFiles,
  isAgentMessage,
  isArtifactPart,
  mapToMessageFiles,
} from '#modules/runs/utils.ts';
import { isImageContentType } from '#utils/helpers.ts';

import { useFileUpload } from '../../files/contexts';
import { AgentProvider } from '../agent/AgentProvider';
import { useMessages } from '../messages';
import { HandsOffContext } from './hands-off-context';

interface Props {
  agent: Agent;
}

export function HandsOffProvider({ agent, children }: PropsWithChildren<Props>) {
  const { messages, setMessages } = useMessages();
  const [stats, setStats] = useState<RunStats>();
  const [logs, setLogs] = useState<RunLog[]>([]);

  const errorHandler = useHandleError();

  const { files, clearFiles } = useFileUpload();
  const { input, isPending, runAgent, stopAgent, reset } = useRunAgent({
    onMessagePart: (event) => {
      const { part } = event;
      const { content, content_type, content_url, metadata } = part;

      const isArtifact = isArtifactPart(part);
      const hasFile = isString(content_url);
      const hasContent = isString(content);
      const hasImage = hasFile && isImageContentType(content_type);

      if (isArtifact) {
        if (hasFile) {
          updateLastAgentMessage((message) => {
            message.files = prepareMessageFiles({ files: message.files, data: part });
          });
        }
      }

      if (hasContent) {
        updateLastAgentMessage((message) => {
          message.rawContent += content;
        });
      }

      if (hasImage) {
        updateLastAgentMessage((message) => {
          message.contentTransforms.push(
            createImageTransform({
              imageUrl: content_url,
              insertAt: message.rawContent.length,
            }),
          );
        });
      }

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
    onMessageCompleted: () => {
      updateLastAgentMessage((message) => {
        message.status = MessageStatus.Completed;
      });
    },
    onStop: () => {
      updateLastAgentMessage((message) => {
        message.status = MessageStatus.Aborted;
      });
    },
    onGeneric: (event) => {
      const log = event.generic;

      setLogs((logs) => [...logs, log]);
    },
    onDone: () => {
      handleDone();
    },
    onRunFailed: (event) => {
      const { error } = event.run;

      handleError(error);

      if (error) {
        setLogs((logs) => [...logs, error]);
      }
    },
  });

  const sourcesData = useMemo(() => extractSources(messages), [messages]);

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

            const citationTransformGroup = message.contentTransforms.find(
              (transform): transform is CitationTransform =>
                transform.kind === MessageContentTransformType.Citation &&
                transform.startIndex === newSource.startIndex,
            );

            message.sources = sources;

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
        default:
          break;
      }
    },
    [updateLastAgentMessage],
  );

  const handleDone = useCallback(() => {
    setStats((stats) => ({ ...stats, endTime: Date.now() }));
  }, []);

  const handleError = useCallback(
    (error: unknown) => {
      const errorCode = getErrorCode(error);

      errorHandler(error, {
        errorToast: { title: errorCode?.toString() ?? 'Failed to run agent.', includeErrorMessage: true },
      });
    },
    [errorHandler],
  );

  const handleClear = useCallback(() => {
    reset();
    setMessages([]);
    setStats(undefined);
    setLogs([]);
    clearFiles();
  }, [reset, setMessages, clearFiles]);

  const previousAgent = usePrevious(agent);
  useEffect(() => {
    if (agent !== previousAgent) {
      handleClear();
    }
  }, [handleClear, agent, previousAgent]);

  const run = useCallback(
    async (input: string) => {
      handleClear();
      setStats({ startTime: Date.now() });

      const uploadFiles = extractValidUploadFiles(files);
      const messageParts = [createMessagePart({ content: input }), ...createFileMessageParts(uploadFiles)];
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
        await runAgent({ agent, messageParts });
      } catch (error) {
        handleError(error);
      }
    },
    [agent, files, runAgent, setMessages, handleError, handleClear, clearFiles],
  );

  const contextValue = useMemo(
    () => ({
      agent,
      input,
      messages,
      stats,
      logs,
      isPending,
      onSubmit: run,
      onCancel: stopAgent,
      onClear: handleClear,
    }),
    [agent, input, messages, stats, logs, isPending, run, stopAgent, handleClear],
  );

  return (
    <SourcesProvider sourcesData={sourcesData}>
      <HandsOffContext.Provider value={contextValue}>
        <AgentProvider agent={agent} isMonitorStatusEnabled={isPending}>
          {children}
        </AgentProvider>
      </HandsOffContext.Provider>
    </SourcesProvider>
  );
}

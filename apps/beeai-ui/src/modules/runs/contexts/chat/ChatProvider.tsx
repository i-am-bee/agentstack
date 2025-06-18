/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import isString from 'lodash/isString';
import type { PropsWithChildren } from 'react';
import { useCallback, useEffect, useMemo } from 'react';
import { v4 as uuid } from 'uuid';

import { useImmerWithGetter } from '#hooks/useImmerWithGetter.ts';
import { usePrevious } from '#hooks/usePrevious.ts';
import type { Agent } from '#modules/agents/api/types.ts';
import { type MessagePartMetadata, MetadataKind } from '#modules/runs/api/types.ts';
import { type AssistantMessage, type ChatMessage, MessageStatus } from '#modules/runs/chat/types.ts';
import { prepareMessageFiles } from '#modules/runs/files/utils.ts';
import { useRunAgent } from '#modules/runs/hooks/useRunAgent.ts';
import { SourcesProvider } from '#modules/runs/sources/contexts/SourcesProvider.tsx';
import { extractSources, prepareMessageSources } from '#modules/runs/sources/utils.ts';
import { Role } from '#modules/runs/types.ts';
import {
  createFileMessageParts,
  createMessagePart,
  extractValidUploadFiles,
  isArtifactPart,
  mapToMessageFiles,
} from '#modules/runs/utils.ts';
import { isImageContentType } from '#utils/helpers.ts';
import { toMarkdownImage } from '#utils/markdown.ts';

import { useFileUpload } from '../../files/contexts';
import { ChatContext, ChatMessagesContext } from './chat-context';

interface Props {
  agent: Agent;
}

export function ChatProvider({ agent, children }: PropsWithChildren<Props>) {
  const [messages, , setMessages] = useImmerWithGetter<ChatMessage[]>([]);

  const { files, clearFiles } = useFileUpload();
  const { isPending, runAgent, stopAgent, reset } = useRunAgent({
    onMessagePart: (event) => {
      const { part } = event;
      const { content, content_type, content_url, metadata } = part;

      const isArtifact = isArtifactPart(part);
      const hasFile = isString(content_url);
      const hasContent = isString(content);
      const hasImage = hasFile && isImageContentType(content_type);

      if (isArtifact) {
        if (hasFile) {
          updateLastAssistantMessage((message) => {
            message.files = prepareMessageFiles({ files: message.files, data: part });
          });
        }
      }

      if (hasContent) {
        updateLastAssistantMessage((message) => {
          message.content += content;
        });
      }

      if (hasImage) {
        updateLastAssistantMessage((message) => {
          message.content += toMarkdownImage(content_url);
        });
      }

      if (metadata) {
        processMetadata(metadata);
      }
    },
    onMessageCompleted: () => {
      updateLastAssistantMessage((message) => {
        message.status = MessageStatus.Completed;
      });
    },
    onStop: () => {
      updateLastAssistantMessage((message) => {
        message.status = MessageStatus.Aborted;
      });
    },
    onRunFailed: (event) => {
      handleError(event.run.error);
    },
  });

  const sourcesData = useMemo(() => extractSources(messages), [messages]);

  const updateLastAssistantMessage = useCallback(
    (updater: (message: AssistantMessage) => void) => {
      setMessages((messages) => {
        const lastMessage = messages.at(-1);

        if (lastMessage?.role === Role.Assistant) {
          updater(lastMessage);
        }
      });
    },
    [setMessages],
  );

  const processMetadata = useCallback(
    (metadata: MessagePartMetadata) => {
      switch (metadata.kind) {
        case MetadataKind.Citation:
          updateLastAssistantMessage((message) => {
            message.sources = prepareMessageSources({ message, metadata });
          });

          break;

        default:
          break;
      }
    },
    [updateLastAssistantMessage],
  );

  const handleError = useCallback(
    (error: unknown) => {
      if (error) {
        updateLastAssistantMessage((message) => {
          message.error = error;
          message.status = MessageStatus.Failed;
        });
      }
    },
    [updateLastAssistantMessage],
  );

  const sendMessage = useCallback(
    async (input: string) => {
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
          role: Role.Assistant,
          content: '',
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
    [agent, files, runAgent, setMessages, handleError, clearFiles],
  );

  const handleClear = useCallback(() => {
    reset();
    setMessages([]);
    clearFiles();
  }, [reset, setMessages, clearFiles]);

  const previousAgent = usePrevious(agent);
  useEffect(() => {
    if (agent !== previousAgent) {
      handleClear();
    }
  }, [handleClear, agent, previousAgent]);

  const contextValue = useMemo(
    () => ({
      agent,
      isPending,
      onCancel: stopAgent,
      onClear: handleClear,
      sendMessage,
    }),
    [agent, isPending, stopAgent, handleClear, sendMessage],
  );

  return (
    <SourcesProvider sourcesData={sourcesData}>
      <ChatContext.Provider value={contextValue}>
        <ChatMessagesContext.Provider value={messages}>{children}</ChatMessagesContext.Provider>
      </ChatContext.Provider>
    </SourcesProvider>
  );
}

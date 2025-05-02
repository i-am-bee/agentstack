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

import type { PropsWithChildren } from 'react';
import { useCallback, useMemo } from 'react';
import { v4 as uuid } from 'uuid';

import { useImmerWithGetter } from '#hooks/useImmerWithGetter.ts';
import type { Agent } from '#modules/agents/api/types.ts';
import { type AssistantMessage, type ChatMessage, MessageStatus } from '#modules/runs/chat/types.ts';
import { useRunAgent } from '#modules/runs/hooks/useRunAgent.ts';
import { Role } from '#modules/runs/types.ts';
import { isArtifact } from '#modules/runs/utils.ts';

import { ChatContext, ChatMessagesContext } from './chat-context';

interface Props {
  agent: Agent;
}

export function ChatProvider({ agent, children }: PropsWithChildren<Props>) {
  const [messages, , setMessages] = useImmerWithGetter<ChatMessage[]>([]);

  const { isPending, runAgent, stopAgent, reset } = useRunAgent({
    onMessagePart: (event) => {
      const { part } = event;

      if (isArtifact(part)) {
        return;
      }

      updateLastAssistantMessage((message) => {
        message.content += part.content;
      });
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
      setMessages((messages) => {
        messages.push({
          key: uuid(),
          role: Role.User,
          content: input,
        });
        messages.push({
          key: uuid(),
          role: Role.Assistant,
          content: '',
          status: MessageStatus.InProgress,
        });
      });

      try {
        await runAgent({ agent, content: input });
      } catch (error) {
        handleError(error);
      }
    },
    [agent, runAgent, setMessages, handleError],
  );

  const handleClear = useCallback(() => {
    reset();
    setMessages([]);
  }, [reset, setMessages]);

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
    <ChatContext.Provider value={contextValue}>
      <ChatMessagesContext.Provider value={messages}>{children}</ChatMessagesContext.Provider>
    </ChatContext.Provider>
  );
}

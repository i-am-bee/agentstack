/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Artifact, ContextHistory, Message } from 'agentstack-sdk';
import { v4 as uuid } from 'uuid';

import { processMessageMetadata, processParts } from '#api/a2a/part-processors.ts';
import { Role } from '#modules/messages/api/types.ts';
import type { UIAgentMessage, UIUserMessage } from '#modules/messages/types.ts';
import { type UIMessage, UIMessageStatus } from '#modules/messages/types.ts';
import { addMessagePart } from '#modules/messages/utils.ts';
import type { TaskId } from '#modules/tasks/api/types.ts';

function isMessage(data: Message | Artifact): data is Message {
  return 'messageId' in data;
}

function processHistoryMessage(message: Message, lastTaskId?: TaskId): UIAgentMessage | UIUserMessage {
  const metadataParts = processMessageMetadata(message);
  const contentParts = processParts(message.parts);
  const parts = [...metadataParts, ...contentParts];
  const taskId = message.taskId ?? lastTaskId;

  if (message.role === 'ROLE_AGENT') {
    const uiMessage: UIAgentMessage = {
      id: message.messageId,
      role: Role.Agent,
      status: UIMessageStatus.Completed,
      taskId,
      parts: [],
    };

    parts.forEach((part) => {
      uiMessage.parts = addMessagePart(part, uiMessage);
    });

    return uiMessage;
  }

  return {
    id: message.messageId,
    role: Role.User,
    taskId,
    parts,
  } satisfies UIUserMessage;
}

function processHistoryArtifact(artifact: Artifact, lastTaskId?: TaskId): UIAgentMessage {
  const contentParts = processParts(artifact.parts);

  return {
    id: uuid(),
    role: Role.Agent,
    status: UIMessageStatus.Completed,
    taskId: lastTaskId,
    parts: contentParts,
  };
}

export function convertHistoryToUIMessages(history: ContextHistory[]): UIMessage[] {
  const { messages } = history.reduce<{ messages: UIMessage[]; taskId?: TaskId }>(
    ({ messages, taskId }, { data }) => {
      let lastTaskId = taskId;

      let message: UIMessage;

      if (isMessage(data)) {
        lastTaskId = data.taskId ?? lastTaskId;
        message = processHistoryMessage(data, lastTaskId);
      } else {
        message = processHistoryArtifact(data, lastTaskId);
      }

      const lastMessage = messages.at(-1);
      const shouldGroup = lastMessage && lastMessage.role === message.role && lastMessage.taskId === message.taskId;

      if (shouldGroup) {
        messages.splice(-1, 1, {
          ...lastMessage,
          parts: [...message.parts, ...lastMessage.parts],
        });
      } else {
        messages.push(message);
      }

      return {
        messages,
        taskId: lastTaskId,
      };
    },
    { messages: [], taskId: undefined },
  );

  return messages;
}

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Artifact, Message } from '@a2a-js/sdk';
import { match } from 'ts-pattern';
import { v4 as uuid } from 'uuid';

import { processMessageMetadata, processParts } from '#api/a2a/part-processors.ts';
import { Role } from '#modules/messages/api/types.ts';
import type { UIAgentMessage, UIUserMessage } from '#modules/messages/types.ts';
import { type UIMessage, UIMessageStatus } from '#modules/messages/types.ts';
import { addTranformedMessagePart } from '#modules/messages/utils.ts';
import type { ContextHistoryItem } from '#modules/platform-context/api/types.ts';
import type { TaskId } from '#modules/tasks/api/types.ts';

export function convertHistoryToUIMessages(history: ContextHistoryItem[]): UIMessage[] {
  const { messages } = history.reduce<{ messages: UIMessage[]; taskId?: TaskId }>(
    (acc, { data }) => {
      let lastTaskId = acc.taskId;

      const message = match(data)
        .with({ kind: 'message' }, (message: Message) => {
          const metadataParts = processMessageMetadata(message);
          const contentParts = processParts(message.parts);
          const parts = [...metadataParts, ...contentParts];

          lastTaskId = message.taskId;

          return match(message)
            .with({ role: 'agent' }, (): UIAgentMessage => {
              const message: UIAgentMessage = {
                id: uuid(),
                role: Role.Agent,
                status: UIMessageStatus.Completed,
                taskId: lastTaskId,
                parts: [],
              };

              parts.forEach((part) => {
                const transformedParts = addTranformedMessagePart(part, message);

                message.parts = transformedParts;
              });

              return message;
            })
            .with(
              { role: 'user' },
              (): UIUserMessage => ({
                id: uuid(),
                role: Role.User,
                taskId: lastTaskId,
                parts,
              }),
            )
            .exhaustive();
        })
        .otherwise((artifact: Artifact): UIAgentMessage => {
          const contentParts = processParts(artifact.parts);

          return {
            id: uuid(),
            role: Role.Agent,
            status: UIMessageStatus.Completed,
            taskId: lastTaskId,
            parts: contentParts,
          };
        });

      const lastMessage = acc.messages.at(-1);
      const shouldGroup = lastMessage && lastMessage.role === message.role && lastMessage.taskId === message.taskId;

      const messages = shouldGroup
        ? [
            ...acc.messages.slice(0, -1),
            {
              ...lastMessage,
              parts: [...lastMessage.parts, ...message.parts],
            },
          ]
        : [...acc.messages, message];

      return {
        messages,
        taskId: lastTaskId,
      };
    },
    { messages: [], taskId: undefined },
  );

  return messages;
}

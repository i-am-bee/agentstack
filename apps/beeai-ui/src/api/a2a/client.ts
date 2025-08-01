/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { TaskStatusUpdateEvent } from '@a2a-js/sdk';
import { A2AClient } from '@a2a-js/sdk/client';
import { Subject } from 'rxjs';
import { match } from 'ts-pattern';

import type { FileEntity } from '#modules/files/types.ts';
import type { UIMessagePart } from '#modules/messages/types.ts';
import type { ContextId } from '#modules/tasks/api/types.ts';
import { getBaseUrl } from '#utils/api/getBaseUrl.ts';
import { isNotNull } from '#utils/helpers.ts';

import { AGENT_ERROR_MESSAGE } from './constants';
import { processFilePart, processMessageMetadata, processTextPart } from './part-processors';
import type { ChatRun } from './types';
import { createUserMessage, extractTextFromMessage } from './utils';

function handleStatusUpdate(event: TaskStatusUpdateEvent): UIMessagePart[] {
  const { message, state } = event.status;

  if (state === 'failed' || state === 'rejected') {
    const errorMessage = extractTextFromMessage(message) ?? AGENT_ERROR_MESSAGE;

    throw new Error(errorMessage);
  }

  if (!message) {
    return [];
  }

  const metadataParts = processMessageMetadata(message);

  const contentParts = message.parts
    .flatMap((part) => {
      const processedParts = match(part)
        .with({ kind: 'text' }, (part) => processTextPart(part))
        .with({ kind: 'file' }, processFilePart)
        .otherwise((otherPart) => {
          console.warn(`Unsupported part - ${otherPart.kind}`);

          return null;
        });

      return processedParts;
    })
    .filter(isNotNull);

  return [...metadataParts, ...contentParts];
}

export const buildA2AClient = (providerId: string) => {
  const agentUrl = `${getBaseUrl()}/api/v1/a2a/${providerId}`;
  const client = new A2AClient(agentUrl);

  const chat = ({ text, files, contextId }: { text: string; files: FileEntity[]; contextId: ContextId }) => {
    const messageSubject = new Subject<UIMessagePart[]>();
    let taskId: string | null = null;

    const iterateOverStream = async () => {
      const stream = client.sendMessageStream({ message: createUserMessage({ text, files, contextId }) });

      for await (const event of stream) {
        match(event)
          .with(
            {
              kind: 'task',
            },
            (task) => {
              taskId = task.id;
            },
          )
          .with({ kind: 'status-update' }, (event) => {
            const messageParts = handleStatusUpdate(event);
            messageSubject.next(messageParts);
          });
      }
      messageSubject.complete();
    };

    const run: ChatRun = {
      done: iterateOverStream(),
      subscribe: (fn) => {
        const subscription = messageSubject.subscribe(fn);

        return () => {
          subscription.unsubscribe();
        };
      },
      cancel: async () => {
        messageSubject.complete();

        if (taskId) {
          await client.cancelTask({ id: taskId });
        }
      },
    };

    return run;
  };

  return { chat };
};

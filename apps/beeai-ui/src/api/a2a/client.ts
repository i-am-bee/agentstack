/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { TaskArtifactUpdateEvent, TaskStatusUpdateEvent } from '@a2a-js/sdk';
import { A2AClient } from '@a2a-js/sdk/client';
import { Subject } from 'rxjs';
import { match } from 'ts-pattern';

import type { UIMessagePart, UIUserMessage } from '#modules/messages/types.ts';
import type { ContextId, TaskId } from '#modules/tasks/api/types.ts';
import { getBaseUrl } from '#utils/api/getBaseUrl.ts';

import { AGENT_ERROR_MESSAGE } from './constants';
import { processMessageMetadata, processParts } from './part-processors';
import type { ChatRun } from './types';
import { createUserMessage, extractTextFromMessage, isArtifactUpdateEvent } from './utils';

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
  const contentParts = processParts(message.parts);

  return [...metadataParts, ...contentParts];
}

function handleArtifactUpdate(event: TaskArtifactUpdateEvent): UIMessagePart[] {
  const { artifact } = event;

  const contentParts = processParts(artifact.parts);

  return contentParts;
}

export const buildA2AClient = (providerId: string) => {
  const agentUrl = `${getBaseUrl()}/api/v1/a2a/${providerId}`;
  const client = new A2AClient(agentUrl);

  const chat = ({ message, contextId }: { message: UIUserMessage; contextId: ContextId }) => {
    const messageSubject = new Subject<{ parts: UIMessagePart[]; taskId: TaskId }>();
    let taskId: string | null = null;

    const iterateOverStream = async () => {
      const stream = client.sendMessageStream({ message: createUserMessage({ message, contextId }) });

      for await (const event of stream) {
        match(event)
          .with({ kind: 'task' }, (task) => {
            taskId = task.id;
          })
          .with({ kind: 'status-update' }, { kind: 'artifact-update' }, (event) => {
            taskId = event.taskId;

            const parts = isArtifactUpdateEvent(event) ? handleArtifactUpdate(event) : handleStatusUpdate(event);

            messageSubject.next({ parts, taskId });
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

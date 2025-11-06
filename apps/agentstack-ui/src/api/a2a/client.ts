/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { TaskArtifactUpdateEvent, TaskStatusUpdateEvent } from '@a2a-js/sdk';
import { A2AClient } from '@a2a-js/sdk/client';
import { handleAgentCard, handleInputRequired, handleTaskStatusUpdate } from 'agentstack-sdk';
import { defaultIfEmpty, filter, lastValueFrom, Subject } from 'rxjs';
import { match } from 'ts-pattern';

import { UnauthenticatedError } from '#api/errors.ts';
import type { UIMessagePart } from '#modules/messages/types.ts';
import type { TaskId } from '#modules/tasks/api/types.ts';
import { getBaseUrl } from '#utils/api/getBaseUrl.ts';

import { AGENT_ERROR_MESSAGE } from './constants';
import { processMessageMetadata, processParts } from './part-processors';
import type { ChatResult, TaskStatusUpdateResultWithTaskId } from './types';
import { type ChatParams, type ChatRun, RunResultType } from './types';
import { createUserMessage, extractTextFromMessage } from './utils';

function handleStatusUpdate<UIGenericPart = never>(
  event: TaskStatusUpdateEvent,
  onStatusUpdate?: (event: TaskStatusUpdateEvent) => UIGenericPart[],
): (UIMessagePart | UIGenericPart)[] {
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

  const genericParts = onStatusUpdate?.(event) || [];

  return [...metadataParts, ...contentParts, ...genericParts];
}

function handleArtifactUpdate(event: TaskArtifactUpdateEvent): UIMessagePart[] {
  const { artifact } = event;

  const contentParts = processParts(artifact.parts);

  return contentParts;
}

export interface CreateA2AClientParams<UIGenericPart = never> {
  providerId: string;
  onStatusUpdate?: (event: TaskStatusUpdateEvent) => UIGenericPart[];
}

export const buildA2AClient = async <UIGenericPart = never>({
  providerId,
  onStatusUpdate,
}: CreateA2AClientParams<UIGenericPart>) => {
  const agentCardUrl = `${getBaseUrl()}/api/v1/a2a/${providerId}/.well-known/agent-card.json`;

  const client = await A2AClient.fromCardUrl(agentCardUrl, { fetchImpl: clientFetch });
  const card = await client.getAgentCard();
  const { resolveMetadata: resolveAgentCardMetadata, demands } = handleAgentCard(card);
  const { resolveMetadata: resolveInputRequiredMetadata } = handleInputRequired();

  const chat = ({ message, contextId, fulfillments, responses, taskId: initialTaskId }: ChatParams) => {
    const messageSubject = new Subject<ChatResult<UIGenericPart>>();

    let taskId: undefined | TaskId = initialTaskId;

    const iterateOverStream = async () => {
      const agentCardMetadata = await resolveAgentCardMetadata(fulfillments);
      const inputRequiredMetadata = await resolveInputRequiredMetadata(responses);

      const metadata = { ...agentCardMetadata, ...inputRequiredMetadata };

      const stream = client.sendMessageStream({
        message: createUserMessage({ message, contextId, metadata, taskId }),
      });

      const taskResult = lastValueFrom(
        messageSubject.asObservable().pipe(
          filter(
            (result: ChatResult): result is TaskStatusUpdateResultWithTaskId => result.type !== RunResultType.Parts,
          ),
          defaultIfEmpty(null),
        ),
      );

      for await (const event of stream) {
        match(event)
          .with({ kind: 'task' }, (task) => {
            taskId = task.id;
          })
          .with({ kind: 'status-update' }, (event) => {
            taskId = event.taskId;

            handleTaskStatusUpdate(event).forEach((result) => {
              if (!taskId) {
                throw new Error(`Illegal State - taskId missing on status-update event`);
              }

              messageSubject.next({
                taskId,
                ...result,
              });
            });

            const parts: (UIMessagePart | UIGenericPart)[] = handleStatusUpdate(event, onStatusUpdate);

            messageSubject.next({ type: RunResultType.Parts, parts, taskId });
          })
          .with({ kind: 'artifact-update' }, (event) => {
            taskId = event.taskId;

            const parts = handleArtifactUpdate(event);

            messageSubject.next({ type: RunResultType.Parts, parts, taskId });
          });
      }

      messageSubject.complete();

      return taskResult;
    };

    const run: ChatRun<UIGenericPart> = {
      taskId,
      done: iterateOverStream(),
      subscribe: (fn) => {
        const subscription = messageSubject
          .asObservable()
          .pipe(
            filter(
              (
                result,
              ): result is { type: RunResultType.Parts; parts: Array<UIMessagePart | UIGenericPart>; taskId: TaskId } =>
                result.type === 'parts',
            ),
          )
          .subscribe(fn);

        return () => {
          subscription.unsubscribe();
        };
      },
      cancel: async () => {
        messageSubject.complete();

        if (taskId) {
          await cancelTask(taskId);
        }
      },
    };

    return run;
  };

  const cancelTask = async (taskId: TaskId) => {
    await client.cancelTask({ id: taskId });
  };

  return {
    chat,
    cancelTask,
    demands,
  };
};

async function clientFetch(input: RequestInfo, init?: RequestInit) {
  const response = await fetch(input, init);
  if (!response.ok && response.status === 401) {
    throw new UnauthenticatedError({ message: 'You are not authenticated.', response });
  }

  return response;
}

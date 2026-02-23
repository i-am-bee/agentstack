/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Client } from '@a2a-js/sdk/client';
import type { Task, TaskArtifactUpdateEvent, TaskStatusUpdateEvent } from 'agentstack-sdk';
import { extractTextFromMessage, handleAgentCard, handleTaskStatusUpdate, resolveUserMetadata } from 'agentstack-sdk';
import { defaultIfEmpty, filter, lastValueFrom, Subject } from 'rxjs';
import { match } from 'ts-pattern';

import { A2AExtensionError, TaskCanceledError } from '#api/errors.ts';
import type { UITextPart } from '#modules/messages/types.ts';
import { type UIMessagePart, UIMessagePartKind } from '#modules/messages/types.ts';
import type { TaskId } from '#modules/tasks/api/types.ts';

import { getAgentClient } from './agent-card';
import { AGENT_ERROR_MESSAGE } from './constants';
import { processArtifactMetadata, processMessageMetadata, processParts } from './part-processors';
import type { ChatResult, TaskStatusUpdateResultWithTaskId } from './types';
import { type ChatParams, type ChatRun, RunResultType } from './types';
import { createUserMessage, extractErrorExtension } from './utils';

function handleStatusUpdate<UIGenericPart = never>(
  event: TaskStatusUpdateEvent,
  onStatusUpdate?: (event: TaskStatusUpdateEvent) => UIGenericPart[],
): (UIMessagePart | UIGenericPart)[] {
  const { message, state } = event.status;
  const extensionError = extractErrorExtension(message?.metadata);

  if (state === 'failed' || state === 'rejected') {
    if (extensionError) {
      throw new A2AExtensionError(extensionError);
    }

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
  const { artifact, taskId } = event;

  const contentParts = processParts(artifact.parts);
  const metadataParts = processArtifactMetadata(artifact, taskId);

  const { artifactId, description, name } = artifact;
  const { textParts, otherParts } = contentParts.reduce<{ textParts: UITextPart[]; otherParts: UIMessagePart[] }>(
    (acc, part) => {
      if (part.kind === UIMessagePartKind.Text) {
        acc.textParts.push(part);
      } else {
        acc.otherParts.push(part);
      }
      return acc;
    },
    { textParts: [], otherParts: [] },
  );

  if (textParts.length === 0 && metadataParts.length === 0) {
    return otherParts;
  }

  return [
    {
      kind: UIMessagePartKind.Artifact,
      artifactId,
      description,
      name,
      taskId,
      parts: [...textParts, ...metadataParts],
    },
    ...otherParts,
  ];
}

async function handleEventError(error: unknown, client: Client, taskId: TaskId | undefined) {
  if (taskId) {
    let task: Task | null = null;

    try {
      task = await client.getTask({ id: taskId });
    } catch (getTaskError) {
      console.warn('Failed to check task status after stream error:', getTaskError);
    }

    if (task?.status.state === 'canceled') {
      throw new TaskCanceledError(taskId);
    }
  }

  throw error;
}

interface CreateA2AClientParams<UIGenericPart = never> {
  providerId: string;
  authToken: string;
  onStatusUpdate?: (event: TaskStatusUpdateEvent) => UIGenericPart[];
}

export const buildA2AClient = async <UIGenericPart = never>({
  providerId,
  authToken,
  onStatusUpdate,
}: CreateA2AClientParams<UIGenericPart>) => {
  const client = await getAgentClient(providerId, authToken);
  const card = await client.getAgentCard();

  const { resolveMetadata: resolveAgentCardMetadata, demands } = handleAgentCard(card);

  const chat = ({ message, contextId, fulfillments, inputs, taskId: initialTaskId }: ChatParams) => {
    const messageSubject = new Subject<ChatResult<UIGenericPart>>();

    let taskId: undefined | TaskId = initialTaskId;

    const iterateOverStream = async () => {
      const agentCardMetadata = await resolveAgentCardMetadata(fulfillments);
      const userMetadata = await resolveUserMetadata(inputs);

      const metadata = { ...agentCardMetadata, ...userMetadata };

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

      try {
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
            })
            .with({ kind: 'message' }, (message) => {
              // For non-streaming agents, a task ID may not be available. In that case,
              // we fall back to using the message ID as a task identifier.
              const resolvedTaskId = message.taskId ?? taskId ?? message.messageId;
              taskId = resolvedTaskId;

              const metadataParts = processMessageMetadata(message);
              const contentParts = processParts(message.parts);
              const parts = [...metadataParts, ...contentParts];

              messageSubject.next({ type: RunResultType.Parts, parts, taskId: resolvedTaskId });
            });
        }
      } catch (error) {
        await handleEventError(error, client, taskId);
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

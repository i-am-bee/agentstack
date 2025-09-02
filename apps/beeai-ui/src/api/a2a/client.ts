/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { TaskArtifactUpdateEvent, TaskStatusUpdateEvent } from '@a2a-js/sdk';
import { A2AClient } from '@a2a-js/sdk/client';
import { defaultIfEmpty, filter, lastValueFrom, Subject } from 'rxjs';
import { match } from 'ts-pattern';

import type { AgentExtension } from '#modules/agents/api/types.ts';
import type { UIMessagePart } from '#modules/messages/types.ts';
import type { TaskId } from '#modules/tasks/api/types.ts';
import { getBaseUrl } from '#utils/api/getBaseUrl.ts';

import { AGENT_ERROR_MESSAGE } from './constants';
import { llmExtension } from './extensions/services/llm';
import { mcpExtension } from './extensions/services/mcp';
import { formExtension, formMessageExtension } from './extensions/ui/form';
import {
  extractServiceExtensionDemands,
  extractUiExtensionData,
  fulfillServiceExtensionDemand,
} from './extensions/utils';
import { processMessageMetadata, processParts } from './part-processors';
import type { ChatResult, FormRequiredResult } from './types';
import { type ChatParams, type ChatRun, RunResultType } from './types';
import { createUserMessage, extractTextFromMessage } from './utils';

const mcpExtensionExtractor = extractServiceExtensionDemands(mcpExtension);
const fulfillMcpDemand = fulfillServiceExtensionDemand(mcpExtension);
const llmExtensionExtractor = extractServiceExtensionDemands(llmExtension);
const fulfillLlmDemand = fulfillServiceExtensionDemand(llmExtension);
const extractForm = extractUiExtensionData(formMessageExtension);

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

interface CreateA2AClientParams<UIGenericPart = never> {
  providerId: string;
  extensions: AgentExtension[];
  onStatusUpdate?: (event: TaskStatusUpdateEvent) => UIGenericPart[];
}

export const buildA2AClient = <UIGenericPart = never>({
  providerId,
  extensions,
  onStatusUpdate,
}: CreateA2AClientParams<UIGenericPart>) => {
  const mcpDemands = mcpExtensionExtractor(extensions);
  const llmDemands = llmExtensionExtractor(extensions);

  const agentUrl = `${getBaseUrl()}/api/v1/a2a/${providerId}`;
  const client = new A2AClient(agentUrl, {
    // TODO: workaround until the a2a-js bug is resolved https://github.com/a2aproject/a2a-js/issues/116
    ...(typeof window !== 'undefined' && { fetchImpl: window.fetch.bind(window) }),
  });

  const chat = ({ message, contextId, fulfillments, taskId: initialTaskId }: ChatParams) => {
    const messageSubject = new Subject<ChatResult<UIGenericPart>>();

    let taskId: TaskId | undefined = initialTaskId;

    const iterateOverStream = async () => {
      let metadata = {};

      if (mcpDemands) {
        metadata = fulfillMcpDemand(metadata, await fulfillments.mcp(mcpDemands));
      }

      if (llmDemands) {
        metadata = fulfillLlmDemand(metadata, await fulfillments.llm(llmDemands));
      }

      if (message.form) {
        metadata = {
          ...metadata,
          [formExtension.getUri()]: message.form.response,
        };
      }

      const stream = client.sendMessageStream({
        message: createUserMessage({ message, contextId, metadata, taskId }),
      });

      const taskResult = lastValueFrom(
        messageSubject.asObservable().pipe(
          filter((result: ChatResult): result is FormRequiredResult => result.type === RunResultType.FormRequired),
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
            if (event.status.state === 'input-required') {
              const form = extractForm(event.status.message?.metadata);
              if (form) {
                messageSubject.next({
                  type: RunResultType.FormRequired,
                  taskId,
                  form,
                });
              } else {
                throw new Error(`Illegal State - form extension data missing on input-required event`);
              }
            }

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
          await client.cancelTask({ id: taskId });
        }
      },
    };

    return run;
  };

  return { chat };
};

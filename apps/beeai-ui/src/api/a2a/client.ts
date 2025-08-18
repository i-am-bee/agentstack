/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { TaskArtifactUpdateEvent, TaskStatusUpdateEvent } from '@a2a-js/sdk';
import { A2AClient } from '@a2a-js/sdk/client';
import { Subject } from 'rxjs';
import { match } from 'ts-pattern';

import type { AgentExtension } from '#api/types.ts';
import type { UIMessagePart } from '#modules/messages/types.ts';
import type { TaskId } from '#modules/tasks/api/types.ts';
import { getBaseUrl } from '#utils/api/getBaseUrl.ts';

import { AGENT_ERROR_MESSAGE } from './constants';
import { llmExtension } from './extensions/services/llm';
import { mcpExtension } from './extensions/services/mcp';
import { extractServiceExtensionDemands, fulfillServiceExtensionDemand } from './extensions/utils';
import { processMessageMetadata, processParts } from './part-processors';
import type { ChatParams, ChatRun } from './types';
import { createUserMessage, extractTextFromMessage } from './utils';

const mcpExtensionExtractor = extractServiceExtensionDemands(mcpExtension);
const fulFillMcpDemand = fulfillServiceExtensionDemand(mcpExtension);
const llmExtensionExtractor = extractServiceExtensionDemands(llmExtension);
const fulfillLlmDemand = fulfillServiceExtensionDemand(llmExtension);

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
  const client = new A2AClient(agentUrl);

  const chat = ({ message, contextId, fulfillments }: ChatParams) => {
    const messageSubject = new Subject<{ parts: (UIMessagePart | UIGenericPart)[]; taskId: TaskId }>();

    let taskId: string | null = null;

    const iterateOverStream = async () => {
      let metadata = {};

      if (mcpDemands) {
        metadata = fulFillMcpDemand(metadata, await fulfillments.mcp(mcpDemands));
      }

      if (llmDemands) {
        metadata = fulfillLlmDemand(metadata, await fulfillments.llm(llmDemands));
      }

      const stream = client.sendMessageStream({ message: createUserMessage({ message, contextId, metadata }) });

      for await (const event of stream) {
        match(event)
          .with({ kind: 'task' }, (task) => {
            taskId = task.id;
          })
          .with({ kind: 'status-update' }, (event) => {
            taskId = event.taskId;

            const parts: (UIMessagePart | UIGenericPart)[] = handleStatusUpdate(event, onStatusUpdate);

            messageSubject.next({ parts, taskId });
          })
          .with({ kind: 'artifact-update' }, (event) => {
            taskId = event.taskId;

            const parts = handleArtifactUpdate(event);

            messageSubject.next({ parts, taskId });
          });
      }
      messageSubject.complete();
    };

    const run: ChatRun<UIGenericPart> = {
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

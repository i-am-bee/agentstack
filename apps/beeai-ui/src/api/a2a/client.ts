/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { AgentExtension, TaskArtifactUpdateEvent, TaskStatusUpdateEvent } from '@a2a-js/sdk';
import { A2AClient } from '@a2a-js/sdk/client';
import {
  activePlatformExtension,
  embeddingExtension,
  extractServiceExtensionDemands,
  extractUiExtensionData,
  formExtension,
  formMessageExtension,
  fulfillServiceExtensionDemand,
  llmExtension,
  mcpExtension,
  oauthProviderExtension,
  oauthRequestExtension,
  secretsExtension,
  secretsMessageExtension,
  settingsExtension,
} from 'beeai-sdk';
import { defaultIfEmpty, filter, lastValueFrom, Subject } from 'rxjs';
import { match } from 'ts-pattern';

import { UnauthenticatedError } from '#api/errors.ts';
import type { UIMessagePart } from '#modules/messages/types.ts';
import type { TaskId } from '#modules/tasks/api/types.ts';
import { getBaseUrl } from '#utils/api/getBaseUrl.ts';

import { AGENT_ERROR_MESSAGE } from './constants';
import { processMessageMetadata, processParts } from './part-processors';
import type { ChatResult, FormRequiredResult, OAuthRequiredResult, SecretRequiredResult } from './types';
import { type ChatParams, type ChatRun, RunResultType } from './types';
import { createUserMessage, extractTextFromMessage } from './utils';

const oauthExtensionExtractor = extractServiceExtensionDemands(oauthProviderExtension);
const fulfillOauthDemand = fulfillServiceExtensionDemand(oauthProviderExtension);

const mcpExtensionExtractor = extractServiceExtensionDemands(mcpExtension);
const fulfillMcpDemand = fulfillServiceExtensionDemand(mcpExtension);

const llmExtensionExtractor = extractServiceExtensionDemands(llmExtension);
const embeddingExtensionExtractor = extractServiceExtensionDemands(embeddingExtension);
const fulfillLlmDemand = fulfillServiceExtensionDemand(llmExtension);
const fulfillEmbeddingDemand = fulfillServiceExtensionDemand(embeddingExtension);
const extractForm = extractUiExtensionData(formMessageExtension);
const settingsExtensionExtractor = extractServiceExtensionDemands(settingsExtension);
const secretsExtensionExtractor = extractServiceExtensionDemands(secretsExtension);
const fulfillSecretDemand = fulfillServiceExtensionDemand(secretsExtension);
const oauthRequestExtensionExtractor = extractUiExtensionData(oauthRequestExtension);
const secretsMessageExtensionExtractor = extractUiExtensionData(secretsMessageExtension);

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
  extensions: AgentExtension[];
  onStatusUpdate?: (event: TaskStatusUpdateEvent) => UIGenericPart[];
}

export const buildA2AClient = async <UIGenericPart = never>({
  providerId,
  extensions,
  onStatusUpdate,
}: CreateA2AClientParams<UIGenericPart>) => {
  const mcpDemands = mcpExtensionExtractor(extensions);
  const llmDemands = llmExtensionExtractor(extensions);
  const oauthDemands = oauthExtensionExtractor(extensions);
  const settingsDemands = settingsExtensionExtractor(extensions);
  const embeddingDemands = embeddingExtensionExtractor(extensions);
  const secretDemands = secretsExtensionExtractor(extensions);

  const agentCardUrl = `${getBaseUrl()}/api/v1/a2a/${providerId}/.well-known/agent-card.json`;

  const client = await A2AClient.fromCardUrl(agentCardUrl, { fetchImpl: clientFetch });

  const chat = ({ message, contextId, fulfillments, taskId: initialTaskId, settings }: ChatParams) => {
    const messageSubject = new Subject<ChatResult<UIGenericPart>>();

    let taskId: undefined | TaskId = initialTaskId;

    const iterateOverStream = async () => {
      let metadata = {};

      metadata = activePlatformExtension(metadata, fulfillments.getContextToken());

      if (mcpDemands) {
        const mcpFullfilment = await fulfillments.mcp(mcpDemands);

        if (mcpFullfilment !== null) {
          metadata = fulfillMcpDemand(metadata, mcpFullfilment);
        }
      }

      if (llmDemands) {
        metadata = fulfillLlmDemand(metadata, await fulfillments.llm(llmDemands));
      }

      if (oauthDemands) {
        const mcpOAuthFullfilment = await fulfillments.oauth(oauthDemands);

        if (mcpOAuthFullfilment !== null) {
          metadata = fulfillOauthDemand(metadata, mcpOAuthFullfilment);
        }
      }

      if (settingsDemands) {
        metadata = {
          ...metadata,
          [settingsExtension.getUri()]: {
            values: settings,
          },
        };
      }

      if (embeddingDemands) {
        metadata = fulfillEmbeddingDemand(metadata, await fulfillments.embedding(embeddingDemands));
      }

      if (secretDemands) {
        const secretFulfillments = await fulfillments.secrets(secretDemands, message.runtimeFullfilledDemands);
        metadata = fulfillSecretDemand(metadata, secretFulfillments);
      }

      if (message.form) {
        metadata = {
          ...metadata,
          [formExtension.getUri()]: message.form.response,
        };
      }

      if (message.auth) {
        metadata = {
          ...metadata,
          [oauthRequestExtension.getUri()]: {
            redirect_uri: message.auth,
          },
        };
      }

      const stream = client.sendMessageStream({
        message: createUserMessage({ message, contextId, metadata, taskId }),
      });

      const taskResult = lastValueFrom(
        messageSubject.asObservable().pipe(
          filter(
            (result: ChatResult): result is FormRequiredResult | OAuthRequiredResult | SecretRequiredResult =>
              result.type !== RunResultType.Parts,
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

            if (event.status.state === 'auth-required') {
              const oauth = oauthRequestExtensionExtractor(event.status.message?.metadata);
              const secret = secretsMessageExtensionExtractor(event.status.message?.metadata);

              if (oauth) {
                messageSubject.next({
                  type: RunResultType.OAuthRequired,
                  taskId,
                  url: oauth.authorization_endpoint_url,
                });
              } else if (secret) {
                messageSubject.next({
                  type: RunResultType.SecretRequired,
                  taskId,
                  secret,
                });
              } else {
                throw new Error(`Illegal State - oauth extension data missing on auth-required event`);
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
    llmDemands: llmDemands?.llm_demands,
    embeddingDemands: embeddingDemands?.embedding_demands,
    mcpDemands: mcpDemands?.mcp_demands,
    settingsDemands,
    secretDemands: secretDemands?.secret_demands,
  };
};

async function clientFetch(input: RequestInfo, init?: RequestInit) {
  const response = await fetch(input, init);
  if (!response.ok && response.status === 401) {
    throw new UnauthenticatedError({ message: 'You are not authenticated.', response });
  }

  return response;
}

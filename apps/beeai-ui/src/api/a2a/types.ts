/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { FormRender, Fulfillments, SecretDemands } from 'beeai-sdk';

import type { UIMessagePart, UIUserMessage } from '#modules/messages/types.ts';
import type { ContextId, TaskId } from '#modules/tasks/api/types.ts';

import type { buildA2AClient } from './client';

export enum RunResultType {
  FormRequired = 'form-required',
  OAuthRequired = 'oauth-required',
  SecretRequired = 'secret-required',
  Parts = 'parts',
}

export interface FormRequiredResult {
  type: RunResultType.FormRequired;
  taskId: TaskId;
  form: FormRender;
}

export interface OAuthRequiredResult {
  type: RunResultType.OAuthRequired;
  taskId: TaskId;
  url: string;
}

export interface SecretRequiredResult {
  type: RunResultType.SecretRequired;
  taskId: TaskId;
  demands: SecretDemands;
}

export interface PartsResult<UIGenericPart = never> {
  type: RunResultType.Parts;
  taskId: TaskId;
  parts: Array<UIMessagePart | UIGenericPart>;
}

export type ChatResult<UIGenericPart = never> =
  | PartsResult<UIGenericPart>
  | FormRequiredResult
  | OAuthRequiredResult
  | SecretRequiredResult;

export interface ChatParams {
  message: UIUserMessage;
  contextId: ContextId;
  fulfillments: Fulfillments;
  taskId?: TaskId;
}

export interface ChatRun<UIGenericPart = never> {
  taskId?: TaskId;
  done: Promise<null | FormRequiredResult | OAuthRequiredResult | SecretRequiredResult>;
  subscribe: (fn: (data: { parts: (UIMessagePart | UIGenericPart)[]; taskId: TaskId }) => void) => () => void;
  cancel: () => Promise<void>;
}

export type AgentA2AClient<UIGenericPart = never> = Awaited<ReturnType<typeof buildA2AClient<UIGenericPart>>>;

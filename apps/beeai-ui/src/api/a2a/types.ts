/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { UIMessagePart, UIUserMessage } from '#modules/messages/types.ts';
import type { ContextToken } from '#modules/platform-context/contexts/platform-context.ts';
import type { AgentRequestSecrets } from '#modules/runs/contexts/agent-secrets/types.ts';
import type { ContextId, TaskId } from '#modules/tasks/api/types.ts';

import type { buildA2AClient } from './client';
import type { EmbeddingDemand, EmbeddingFulfillment } from './extensions/services/embedding';
import type { LLMDemand, LLMFulfillment } from './extensions/services/llm';
import type { MCPDemand, MCPFulfillment } from './extensions/services/mcp';
import type { OAuthDemand, OAuthFulfillment } from './extensions/services/oauth-provider';
import type { SecretDemands, SecretFulfillment } from './extensions/services/secrets';
import type { FormRender } from './extensions/ui/form';
import type { AgentSettings } from './extensions/ui/settings';

export enum RunResultType {
  FormRequired = 'form-required',
  OAuthRequired = 'oauth-required',
  SecretRequired = 'secret-required',
  Parts = 'parts',
  Artifact = 'artifact',
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
  secret: SecretDemands;
}

export interface ArtifactResult<UIGenericPart = never> {
  type: RunResultType.Artifact;
  artifactId: string;
  taskId: TaskId;
  parts: Array<UIMessagePart | UIGenericPart>;
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
  | SecretRequiredResult
  | ArtifactResult<UIGenericPart>;

export interface ChatParams {
  message: UIUserMessage;
  contextId: ContextId;
  fulfillments: Fulfillments;
  settings?: AgentSettings;
  taskId?: TaskId;
  artifact:
    | {
        start_index: number;
        end_index: number;
        artifact_id: string;
      }
    | undefined;
}

export interface ChatRun<UIGenericPart = never> {
  taskId?: TaskId;
  done: Promise<null | FormRequiredResult | OAuthRequiredResult | SecretRequiredResult>;
  subscribe: (
    fn: (data: { parts: (UIMessagePart | UIGenericPart)[]; taskId: TaskId; artifactId?: string }) => void,
  ) => () => void;
  cancel: () => Promise<void>;
}

export interface Fulfillments {
  mcp: (demand: MCPDemand) => Promise<MCPFulfillment | null>;
  llm: (demand: LLMDemand) => Promise<LLMFulfillment>;
  oauth: (demand: OAuthDemand) => Promise<OAuthFulfillment | null>;
  getContextToken: () => ContextToken;
  embedding: (demand: EmbeddingDemand) => Promise<EmbeddingFulfillment>;
  secrets: (demand: SecretDemands, runtimeFullfilledDemands?: AgentRequestSecrets) => Promise<SecretFulfillment>;
}

export type AgentA2AClient<UIGenericPart = never> = Awaited<ReturnType<typeof buildA2AClient<UIGenericPart>>>;

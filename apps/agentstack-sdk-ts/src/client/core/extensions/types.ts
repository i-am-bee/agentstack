/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { z } from 'zod';

import type { OAuthDemands, OAuthFulfillments } from '../../a2a/extensions/auth/oauth/types';
import type { SecretDemands, SecretFulfillments } from '../../a2a/extensions/auth/secrets/types';
import type { FormRender, FormValues } from '../../a2a/extensions/common/form/types';
import type { ApprovalRequest, ApprovalResponse } from '../../a2a/extensions/interactions/approval/types';
import type { EmbeddingDemands, EmbeddingFulfillments } from '../../a2a/extensions/services/embedding/types';
import type { FormDemands, FormFulfillments } from '../../a2a/extensions/services/form/types';
import type { LLMDemands, LLMFulfillments } from '../../a2a/extensions/services/llm/types';
import type { MCPDemands, MCPFulfillments } from '../../a2a/extensions/services/mcp/types';
import type { CanvasEditRequest } from '../../a2a/extensions/ui/canvas/types';
import type { SettingsDemands, SettingsFulfillments } from '../../a2a/extensions/ui/settings/types';
import type { ContextToken } from '../../api/contexts/types';

export interface A2AExtension<U extends string> {
  getUri: () => U;
}

export interface A2AUiExtension<U extends string, D> extends A2AExtension<U> {
  getMessageMetadataSchema: () => z.ZodSchema<Partial<Record<U, D>>>;
}

export interface A2AServiceExtension<U extends string, D, F> extends A2AExtension<U> {
  getDemandsSchema: () => z.ZodSchema<D>;
  getFulfillmentsSchema: () => z.ZodSchema<F>;
}

export type Fulfillments = Partial<{
  llm: (demand: LLMDemands) => Promise<LLMFulfillments>;
  embedding: (demand: EmbeddingDemands) => Promise<EmbeddingFulfillments>;
  mcp: (demand: MCPDemands) => Promise<MCPFulfillments>;
  oauth: (demand: OAuthDemands) => Promise<OAuthFulfillments>;
  settings: (demand: SettingsDemands) => Promise<SettingsFulfillments>;
  secrets: (demand: SecretDemands) => Promise<SecretFulfillments>;
  form: (demand: FormDemands) => Promise<FormFulfillments>;
  oauthRedirectUri: () => string | null;
  /**
   * @deprecated - keeping this for backwards compatibility, context token is now passed via A2A client headers
   */
  getContextToken: () => ContextToken;
}>;

export type UserMetadataInputs = Partial<{
  form: FormValues;
  canvasEditRequest: CanvasEditRequest;
  approvalResponse: ApprovalResponse;
}>;

export enum TaskStatusUpdateType {
  SecretRequired = 'secret-required',
  FormRequired = 'form-required',
  OAuthRequired = 'oauth-required',
  ApprovalRequired = 'approval-required',
  TextInputRequired = 'text-input-required',
}

export interface SecretRequiredResult {
  type: TaskStatusUpdateType.SecretRequired;
  demands: SecretDemands;
}

export interface FormRequiredResult {
  type: TaskStatusUpdateType.FormRequired;
  form: FormRender;
}

export interface OAuthRequiredResult {
  type: TaskStatusUpdateType.OAuthRequired;
  url: string;
}

export interface ApprovalRequiredResult {
  type: TaskStatusUpdateType.ApprovalRequired;
  request: ApprovalRequest;
}

export interface TextInputRequiredResult {
  type: TaskStatusUpdateType.TextInputRequired;
  text: string;
}

export type TaskStatusUpdateResult =
  | SecretRequiredResult
  | FormRequiredResult
  | OAuthRequiredResult
  | ApprovalRequiredResult
  | TextInputRequiredResult;

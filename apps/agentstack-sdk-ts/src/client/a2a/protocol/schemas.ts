/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

import { a2aSchema } from './utils';

// --- Agent Card ---

export const agentInterfaceSchema = a2aSchema(
  z.object({
    url: z.string(),
    protocolBinding: z.string().optional(),
    tenant: z.string().optional(),
    protocolVersion: z.string().optional(),
  }),
);

export const agentExtensionSchema = a2aSchema(
  z.object({
    uri: z.string(),
    description: z.string().optional(),
    required: z.boolean().optional(),
    params: z.record(z.string(), z.unknown()).optional(),
  }),
);

export const agentCapabilitiesSchema = a2aSchema(
  z.object({
    streaming: z.boolean().optional(),
    pushNotifications: z.boolean().optional(),
    extensions: z.array(agentExtensionSchema).optional(),
    extendedAgentCard: z.boolean().optional(),
  }),
);

export const agentProviderSchema = a2aSchema(
  z.object({
    url: z.string(),
    organization: z.string(),
  }),
);

export const agentCardSignatureSchema = a2aSchema(
  z.object({
    protected: z.string(),
    signature: z.string(),
    header: z.record(z.string(), z.unknown()).optional(),
  }),
);

export const agentSkillSchema = a2aSchema(
  z.object({
    id: z.string(),
    name: z.string(),
    description: z.string(),
    tags: z.array(z.string()),
    examples: z.array(z.string()).optional(),
    inputModes: z.array(z.string()).optional(),
    outputModes: z.array(z.string()).optional(),
    securityRequirements: z.array(z.record(z.string(), z.unknown())).optional(),
  }),
);

// --- Security Schemes ---

export const authorizationCodeOAuthFlowSchema = a2aSchema(
  z.object({
    authorizationUrl: z.string(),
    tokenUrl: z.string(),
    refreshUrl: z.string().optional(),
    scopes: z.record(z.string(), z.string()),
    pkceRequired: z.boolean().optional(),
  }),
);

export const clientCredentialsOAuthFlowSchema = a2aSchema(
  z.object({
    tokenUrl: z.string(),
    refreshUrl: z.string().optional(),
    scopes: z.record(z.string(), z.string()),
  }),
);

export const implicitOAuthFlowSchema = a2aSchema(
  z.object({
    authorizationUrl: z.string(),
    refreshUrl: z.string().optional(),
    scopes: z.record(z.string(), z.string()),
  }),
);

export const passwordOAuthFlowSchema = a2aSchema(
  z.object({
    tokenUrl: z.string(),
    refreshUrl: z.string().optional(),
    scopes: z.record(z.string(), z.string()),
  }),
);

export const deviceCodeOAuthFlowSchema = a2aSchema(
  z.object({
    deviceAuthorizationUrl: z.string(),
    tokenUrl: z.string(),
    refreshUrl: z.string().optional(),
    scopes: z.record(z.string(), z.string()),
  }),
);

export const oauthFlowsSchema = a2aSchema(
  z.object({
    authorizationCode: authorizationCodeOAuthFlowSchema.optional(),
    clientCredentials: clientCredentialsOAuthFlowSchema.optional(),
    implicit: implicitOAuthFlowSchema.optional(),
    password: passwordOAuthFlowSchema.optional(),
    deviceCode: deviceCodeOAuthFlowSchema.optional(),
  }),
);

export const apiKeySecuritySchemeSchema = a2aSchema(
  z.object({
    description: z.string().optional(),
    location: z.string(),
    name: z.string(),
  }),
);

export const httpAuthSecuritySchemeSchema = a2aSchema(
  z.object({
    description: z.string().optional(),
    scheme: z.string(),
    bearerFormat: z.string().optional(),
  }),
);

export const oauth2SecuritySchemeSchema = a2aSchema(
  z.object({
    description: z.string().optional(),
    flows: oauthFlowsSchema,
    oauth2MetadataUrl: z.string().optional(),
  }),
);

export const openIdConnectSecuritySchemeSchema = a2aSchema(
  z.object({
    description: z.string().optional(),
    openIdConnectUrl: z.string(),
  }),
);

export const mutualTlsSecuritySchemeSchema = a2aSchema(
  z.object({
    description: z.string().optional(),
  }),
);

// SecurityScheme uses protobuf oneof — exactly one key is present
export const securitySchemeSchema = a2aSchema(
  z.object({
    apiKeySecurityScheme: apiKeySecuritySchemeSchema.optional(),
    httpAuthSecurityScheme: httpAuthSecuritySchemeSchema.optional(),
    oauth2SecurityScheme: oauth2SecuritySchemeSchema.optional(),
    openIdConnectSecurityScheme: openIdConnectSecuritySchemeSchema.optional(),
    mtlsSecurityScheme: mutualTlsSecuritySchemeSchema.optional(),
  }),
);

export const securityRequirementSchema = a2aSchema(
  z.object({
    schemes: z.record(z.string(), z.object({ list: z.array(z.string()).optional() })).optional(),
  }),
);

export const agentCardSchema = a2aSchema(
  z.object({
    name: z.string(),
    description: z.string(),
    supportedInterfaces: z.array(agentInterfaceSchema).optional(),
    provider: agentProviderSchema.optional(),
    version: z.string(),
    documentationUrl: z.string().optional(),
    capabilities: agentCapabilitiesSchema,
    securitySchemes: z.record(z.string(), securitySchemeSchema).optional(),
    securityRequirements: z.array(securityRequirementSchema).optional(),
    defaultInputModes: z.array(z.string()).optional(),
    defaultOutputModes: z.array(z.string()).optional(),
    skills: z.array(agentSkillSchema).optional(),
    signatures: z.array(agentCardSignatureSchema).optional(),
    iconUrl: z.string().optional(),
  }),
);

// --- Parts ---

export const textPartSchema = a2aSchema(
  z.object({
    text: z.string(),
    metadata: z.record(z.string(), z.unknown()).optional(),
    filename: z.string().optional(),
    mediaType: z.string().optional(),
  }),
);

export const filePartSchema = a2aSchema(
  z.object({
    url: z.string().optional(),
    raw: z.string().optional(),
    metadata: z.record(z.string(), z.unknown()).optional(),
    filename: z.string().optional(),
    mediaType: z.string().optional(),
  }),
);

export const dataPartSchema = a2aSchema(
  z.object({
    data: z.unknown(),
    metadata: z.record(z.string(), z.unknown()).optional(),
    filename: z.string().optional(),
    mediaType: z.string().optional(),
  }),
);

// Part is a union — discriminated by presence of `text`, `url`/`raw`, or `data`
export const partSchema = a2aSchema(z.union([textPartSchema, filePartSchema, dataPartSchema]));

// --- Artifacts ---

export const artifactSchema = a2aSchema(
  z.object({
    artifactId: z.string(),
    name: z.string().optional(),
    description: z.string().optional(),
    parts: z.array(partSchema).default([]),
    metadata: z.record(z.string(), z.unknown()).optional(),
    extensions: z.array(z.string()).optional(),
  }),
);

// --- Messages ---

export const messageSchema = a2aSchema(
  z.object({
    messageId: z.string(),
    contextId: z.string().optional(),
    taskId: z.string().optional(),
    role: z.enum(['ROLE_USER', 'ROLE_AGENT', 'ROLE_UNSPECIFIED']),
    parts: z.array(partSchema).default([]),
    metadata: z.record(z.string(), z.unknown()).optional(),
    extensions: z.array(z.string()).optional(),
    referenceTaskIds: z.array(z.string()).optional(),
  }),
);

// --- Task Status ---

export const taskStatusSchema = a2aSchema(
  z.object({
    state: z.enum([
      'TASK_STATE_UNSPECIFIED',
      'TASK_STATE_SUBMITTED',
      'TASK_STATE_WORKING',
      'TASK_STATE_COMPLETED',
      'TASK_STATE_FAILED',
      'TASK_STATE_CANCELED',
      'TASK_STATE_INPUT_REQUIRED',
      'TASK_STATE_REJECTED',
      'TASK_STATE_AUTH_REQUIRED',
    ]),
    message: messageSchema.optional(),
    timestamp: z.string().optional(),
  }),
);

// --- Events ---

export const taskStatusUpdateEventSchema = a2aSchema(
  z.object({
    taskId: z.string(),
    contextId: z.string(),
    status: taskStatusSchema,
    metadata: z.record(z.string(), z.unknown()).optional(),
  }),
);

export const taskSchema = a2aSchema(
  z.object({
    id: z.string(),
    contextId: z.string(),
    status: taskStatusSchema,
    artifacts: z.array(artifactSchema).optional(),
    history: z.array(messageSchema).optional(),
    metadata: z.record(z.string(), z.unknown()).optional(),
  }),
);

export const taskArtifactUpdateEventSchema = a2aSchema(
  z.object({
    taskId: z.string(),
    contextId: z.string(),
    artifact: artifactSchema,
    append: z.boolean().optional(),
    lastChunk: z.boolean().optional(),
    metadata: z.record(z.string(), z.unknown()).optional(),
  }),
);

// --- Stream Response (oneof wrapper for streaming events) ---

export const streamResponseSchema = a2aSchema(
  z.union([
    z.object({ task: taskSchema }),
    z.object({ statusUpdate: taskStatusUpdateEventSchema }),
    z.object({ artifactUpdate: taskArtifactUpdateEventSchema }),
    z.object({ message: messageSchema }),
  ]),
);

// --- JSONRPC Errors ---

const errorBaseSchema = z.object({
  message: z.string(),
  data: z.record(z.string(), z.unknown()).optional(),
});

export const jsonRpcErrorSchema = a2aSchema(
  errorBaseSchema.extend({
    code: z.number(),
  }),
);

export const jsonParseErrorSchema = a2aSchema(
  errorBaseSchema.extend({
    code: z.literal(-32700),
  }),
);

export const invalidRequestErrorSchema = a2aSchema(
  errorBaseSchema.extend({
    code: z.literal(-32600),
  }),
);

export const methodNotFoundErrorSchema = a2aSchema(
  errorBaseSchema.extend({
    code: z.literal(-32601),
  }),
);

export const invalidParamsErrorSchema = a2aSchema(
  errorBaseSchema.extend({
    code: z.literal(-32602),
  }),
);

export const internalErrorSchema = a2aSchema(
  errorBaseSchema.extend({
    code: z.literal(-32603),
  }),
);

export const taskNotFoundErrorSchema = a2aSchema(
  errorBaseSchema.extend({
    code: z.literal(-32001),
  }),
);

export const taskNotCancelableErrorSchema = a2aSchema(
  errorBaseSchema.extend({
    code: z.literal(-32002),
  }),
);

export const pushNotificationNotSupportedErrorSchema = a2aSchema(
  errorBaseSchema.extend({
    code: z.literal(-32003),
  }),
);

export const unsupportedOperationErrorSchema = a2aSchema(
  errorBaseSchema.extend({
    code: z.literal(-32004),
  }),
);

export const contentTypeNotSupportedErrorSchema = a2aSchema(
  errorBaseSchema.extend({
    code: z.literal(-32005),
  }),
);

export const invalidAgentResponseErrorSchema = a2aSchema(
  errorBaseSchema.extend({
    code: z.literal(-32006),
  }),
);

export const authenticatedExtendedCardNotConfiguredErrorSchema = a2aSchema(
  errorBaseSchema.extend({
    code: z.literal(-32007),
  }),
);

export const jsonRpcErrorResponseSchema = a2aSchema(
  z.object({
    jsonrpc: z.literal('2.0'),
    id: z.union([z.string(), z.number()]).nullable(),
    error: z.union([
      jsonRpcErrorSchema,
      jsonParseErrorSchema,
      invalidRequestErrorSchema,
      methodNotFoundErrorSchema,
      invalidParamsErrorSchema,
      internalErrorSchema,
      taskNotFoundErrorSchema,
      taskNotCancelableErrorSchema,
      pushNotificationNotSupportedErrorSchema,
      unsupportedOperationErrorSchema,
      contentTypeNotSupportedErrorSchema,
      invalidAgentResponseErrorSchema,
      authenticatedExtendedCardNotConfiguredErrorSchema,
    ]),
  }),
);

export const getTaskSuccessResponseSchema = a2aSchema(
  z.object({
    jsonrpc: z.literal('2.0'),
    id: z.union([z.string(), z.number()]).nullable(),
    result: taskSchema,
  }),
);

export const getTaskResponseSchema = a2aSchema(z.union([jsonRpcErrorResponseSchema, getTaskSuccessResponseSchema]));

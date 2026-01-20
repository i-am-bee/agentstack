/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

import { a2aSchema } from './utils';

export const agentInterfaceSchema = a2aSchema(
  z.object({
    transport: z.string(),
    url: z.string(),
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
    extensions: z.array(agentExtensionSchema).optional(),
    pushNotifications: z.boolean().optional(),
    stateTransitionHistory: z.boolean().optional(),
    streaming: z.boolean().optional(),
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
    signature: z.string(),
    protected: z.string(),
    header: z.record(z.string(), z.unknown()).optional(),
  }),
);

export const agentSkillSchema = a2aSchema(
  z.object({
    id: z.string(),
    name: z.string(),
    description: z.string(),
    tags: z.array(z.string()),
    inputModes: z.array(z.string()).optional(),
    outputModes: z.array(z.string()).optional(),
    examples: z.array(z.string()).optional(),
    security: z.array(z.record(z.string(), z.array(z.string()))).optional(),
  }),
);

export const authorizationCodeOAuthFlowSchema = a2aSchema(
  z.object({
    authorizationUrl: z.string(),
    tokenUrl: z.string(),
    scopes: z.record(z.string(), z.string()),
    refreshUrl: z.string().optional(),
  }),
);

export const clientCredentialsOAuthFlowSchema = a2aSchema(
  z.object({
    tokenUrl: z.string(),
    scopes: z.record(z.string(), z.string()),
    refreshUrl: z.string().optional(),
  }),
);

export const implicitOAuthFlowSchema = a2aSchema(
  z.object({
    authorizationUrl: z.string(),
    scopes: z.record(z.string(), z.string()),
    refreshUrl: z.string().optional(),
  }),
);

export const passwordOAuthFlowSchema = a2aSchema(
  z.object({
    tokenUrl: z.string(),
    scopes: z.record(z.string(), z.string()),
    refreshUrl: z.string().optional(),
  }),
);

export const oauthFlowsSchema = a2aSchema(
  z.object({
    authorizationCode: authorizationCodeOAuthFlowSchema.optional(),
    clientCredentials: clientCredentialsOAuthFlowSchema.optional(),
    implicit: implicitOAuthFlowSchema.optional(),
    password: passwordOAuthFlowSchema.optional(),
  }),
);

export const apiKeySecuritySchemeSchema = a2aSchema(
  z.object({
    type: z.literal('apiKey'),
    name: z.string(),
    in: z.literal(['cookie', 'header', 'query']),
    description: z.string().optional(),
  }),
);

export const httpAuthSecuritySchemeSchema = a2aSchema(
  z.object({
    type: z.literal('http'),
    scheme: z.string(),
    description: z.string().optional(),
    bearerFormat: z.string().optional(),
  }),
);

export const oauth2SecuritySchemeSchema = a2aSchema(
  z.object({
    type: z.literal('oauth2'),
    flows: oauthFlowsSchema,
    description: z.string().optional(),
    oauth2MetadataUrl: z.string().optional(),
  }),
);

export const openIdConnectSecuritySchemeSchema = a2aSchema(
  z.object({
    type: z.literal('openIdConnect'),
    openIdConnectUrl: z.string(),
    description: z.string().optional(),
  }),
);

export const mutualTlsSecuritySchemeSchema = a2aSchema(
  z.object({
    type: z.literal('mutualTLS'),
    description: z.string().optional(),
  }),
);

export const securitySchemeSchema = a2aSchema(
  z.union([
    apiKeySecuritySchemeSchema,
    httpAuthSecuritySchemeSchema,
    oauth2SecuritySchemeSchema,
    openIdConnectSecuritySchemeSchema,
    mutualTlsSecuritySchemeSchema,
  ]),
);

export const agentCardSchema = a2aSchema(
  z.object({
    url: z.string(),
    name: z.string(),
    description: z.string(),
    version: z.string(),
    protocolVersion: z.string(),
    capabilities: agentCapabilitiesSchema,
    defaultInputModes: z.array(z.string()),
    defaultOutputModes: z.array(z.string()),
    skills: z.array(agentSkillSchema),
    iconUrl: z.string().optional(),
    documentationUrl: z.string().optional(),
    preferredTransport: z.string().optional(),
    supportsAuthenticatedExtendedCard: z.boolean().optional(),
    additionalInterfaces: z.array(agentInterfaceSchema).optional(),
    provider: agentProviderSchema.optional(),
    signatures: z.array(agentCardSignatureSchema).optional(),
    security: z.array(z.record(z.string(), z.array(z.string()))).optional(),
    securitySchemes: z.record(z.string(), securitySchemeSchema).optional(),
  }),
);

export const fileWithBytesSchema = a2aSchema(
  z.object({
    bytes: z.string(),
    mimeType: z.string().optional(),
    name: z.string().optional(),
  }),
);

export const fileWithUriSchema = a2aSchema(
  z.object({
    uri: z.string(),
    mimeType: z.string().optional(),
    name: z.string().optional(),
  }),
);

export const textPartSchema = a2aSchema(
  z.object({
    kind: z.literal('text'),
    text: z.string(),
    metadata: z.record(z.string(), z.unknown()).optional(),
  }),
);

export const filePartSchema = a2aSchema(
  z.object({
    kind: z.literal('file'),
    file: z.union([fileWithBytesSchema, fileWithUriSchema]),
    metadata: z.record(z.string(), z.unknown()).optional(),
  }),
);

export const dataPartSchema = a2aSchema(
  z.object({
    kind: z.literal('data'),
    data: z.record(z.string(), z.unknown()),
    metadata: z.record(z.string(), z.unknown()).optional(),
  }),
);

export const partSchema = a2aSchema(z.union([textPartSchema, filePartSchema, dataPartSchema]));

export const artifactSchema = a2aSchema(
  z.object({
    artifactId: z.string(),
    parts: z.array(partSchema),
    description: z.string().optional(),
    extensions: z.array(z.string()).optional(),
    metadata: z.record(z.string(), z.unknown()).optional(),
    name: z.string().optional(),
  }),
);

export const messageSchema = a2aSchema(
  z.object({
    kind: z.literal('message'),
    messageId: z.string(),
    parts: z.array(partSchema),
    role: z.literal(['agent', 'user']),
    contextId: z.string().optional(),
    extensions: z.array(z.string()).optional(),
    metadata: z.record(z.string(), z.unknown()).optional(),
    referenceTaskIds: z.array(z.string()).optional(),
    taskId: z.string().optional(),
  }),
);

export const taskStatusSchema = a2aSchema(
  z.object({
    state: z.literal([
      'submitted',
      'working',
      'input-required',
      'completed',
      'canceled',
      'failed',
      'rejected',
      'auth-required',
      'unknown',
    ]),
    message: messageSchema.optional(),
    timestamp: z.string().optional(),
  }),
);

export const taskStatusUpdateEventSchema = a2aSchema(
  z.object({
    kind: z.literal('status-update'),
    taskId: z.string(),
    contextId: z.string(),
    status: taskStatusSchema,
    final: z.boolean(),
    metadata: z.record(z.string(), z.unknown()).optional(),
  }),
);

export const taskSchema = a2aSchema(
  z.object({
    kind: z.literal('task'),
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
    kind: z.literal('artifact-update'),
    taskId: z.string(),
    contextId: z.string(),
    artifact: artifactSchema,
    append: z.boolean().optional(),
    lastChunk: z.boolean().optional(),
    metadata: z.record(z.string(), z.unknown()).optional(),
  }),
);

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

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

export const agentInterfaceSchema = z.object({
  transport: z.string(),
  url: z.string(),
});

export const agentExtensionSchema = z.object({
  uri: z.string(),
  description: z.string().optional(),
  required: z.boolean().optional(),
  params: z.record(z.string(), z.unknown()).optional(),
});

export const agentCapabilitiesSchema = z.object({
  extensions: z.array(agentExtensionSchema).optional(),
  pushNotifications: z.boolean().optional(),
  stateTransitionHistory: z.boolean().optional(),
  streaming: z.boolean().optional(),
});

export const agentProviderSchema = z.object({
  url: z.string(),
  organization: z.string(),
});

export const agentCardSignatureSchema = z.object({
  signature: z.string(),
  protected: z.string(),
  header: z.record(z.string(), z.unknown()).optional(),
});

export const agentSkillSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  tags: z.array(z.string()),
  inputModes: z.array(z.string()).optional(),
  outputModes: z.array(z.string()).optional(),
  examples: z.array(z.string()).optional(),
  security: z.array(z.record(z.string(), z.array(z.string()))).optional(),
});

export const authorizationCodeOAuthFlowSchema = z.object({
  authorizationUrl: z.string(),
  tokenUrl: z.string(),
  scopes: z.record(z.string(), z.string()),
  refreshUrl: z.string().optional(),
});

export const clientCredentialsOAuthFlowSchema = z.object({
  tokenUrl: z.string(),
  scopes: z.record(z.string(), z.string()),
  refreshUrl: z.string().optional(),
});

export const implicitOAuthFlowSchema = z.object({
  authorizationUrl: z.string(),
  scopes: z.record(z.string(), z.string()),
  refreshUrl: z.string().optional(),
});

export const passwordOAuthFlowSchema = z.object({
  tokenUrl: z.string(),
  scopes: z.record(z.string(), z.string()),
  refreshUrl: z.string().optional(),
});

export const oAuthFlowsSchema = z.object({
  authorizationCode: authorizationCodeOAuthFlowSchema.optional(),
  clientCredentials: clientCredentialsOAuthFlowSchema.optional(),
  implicit: implicitOAuthFlowSchema.optional(),
  password: passwordOAuthFlowSchema.optional(),
});

export const apiKeySecuritySchemeSchema = z.object({
  type: z.literal('apiKey'),
  name: z.string(),
  in: z.literal(['cookie', 'header', 'query']),
  description: z.string().optional(),
});

export const httpAuthSecuritySchemeSchema = z.object({
  type: z.literal('http'),
  scheme: z.string(),
  description: z.string().optional(),
  bearerFormat: z.string().optional(),
});

export const oAuth2SecuritySchemeSchema = z.object({
  type: z.literal('oauth2'),
  flows: oAuthFlowsSchema,
  description: z.string().optional(),
  oauth2MetadataUrl: z.string().optional(),
});

export const openIdConnectSecuritySchemeSchema = z.object({
  type: z.literal('openIdConnect'),
  openIdConnectUrl: z.string(),
  description: z.string().optional(),
});

export const mutualTlsSecuritySchemeSchema = z.object({
  type: z.literal('mutualTLS'),
  description: z.string().optional(),
});

export const securitySchemeSchema = z.union([
  apiKeySecuritySchemeSchema,
  httpAuthSecuritySchemeSchema,
  oAuth2SecuritySchemeSchema,
  openIdConnectSecuritySchemeSchema,
  mutualTlsSecuritySchemeSchema,
]);

export const agentCardSchema = z.object({
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
});

export const textPartSchema = z.object({
  kind: z.literal('text'),
  text: z.string(),
  metadata: z.record(z.string(), z.unknown()).optional(),
});

export const fileWithBytesSchema = z.object({
  bytes: z.string(),
  mimeType: z.string().optional(),
  name: z.string().optional(),
});

export const fileWithUriSchema = z.object({
  uri: z.string(),
  mimeType: z.string().optional(),
  name: z.string().optional(),
});

export const filePartSchema = z.object({
  kind: z.literal('file'),
  file: z.union([fileWithBytesSchema, fileWithUriSchema]),
  metadata: z.record(z.string(), z.unknown()).optional(),
});

export const dataPartSchema = z.object({
  kind: z.literal('data'),
  data: z.record(z.string(), z.unknown()),
  metadata: z.record(z.string(), z.unknown()).optional(),
});

export const partSchema = z.union([textPartSchema, filePartSchema, dataPartSchema]);

export const artifactSchema = z.object({
  artifactId: z.string(),
  parts: z.array(partSchema),
  description: z.string().optional(),
  extensions: z.array(z.string()).optional(),
  metadata: z.record(z.string(), z.unknown()).optional(),
  name: z.string().optional(),
});

export const messageSchema = z.object({
  kind: z.literal('message'),
  messageId: z.string(),
  parts: z.array(partSchema),
  role: z.literal(['agent', 'user']),
  contextId: z.string().optional(),
  extensions: z.array(z.string()).optional(),
  metadata: z.record(z.string(), z.unknown()).optional(),
  referenceTaskIds: z.array(z.string()).optional(),
  taskId: z.string().optional(),
});

export const taskStatusSchema = z.object({
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
});

export const taskStatusUpdateEventSchema = z.object({
  kind: z.literal('status-update'),
  taskId: z.string(),
  contextId: z.string(),
  status: taskStatusSchema,
  final: z.boolean(),
  metadata: z.record(z.string(), z.unknown()).optional(),
});

export const taskSchema = z.object({
  kind: z.literal('task'),
  id: z.string(),
  contextId: z.string(),
  status: taskStatusSchema,
  artifacts: z.array(artifactSchema).optional(),
  history: z.array(messageSchema).optional(),
  metadata: z.record(z.string(), z.unknown()).optional(),
});

export const taskArtifactUpdateEventSchema = z.object({
  kind: z.literal('artifact-update'),
  taskId: z.string(),
  contextId: z.string(),
  artifact: artifactSchema,
  append: z.boolean().optional(),
  lastChunk: z.boolean().optional(),
  metadata: z.record(z.string(), z.unknown()).optional(),
});

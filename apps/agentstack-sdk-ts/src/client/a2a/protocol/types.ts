/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type z from 'zod';

import type {
  agentCapabilitiesSchema,
  agentCardSchema,
  agentCardSignatureSchema,
  agentExtensionSchema,
  agentInterfaceSchema,
  agentProviderSchema,
  agentSkillSchema,
  apiKeySecuritySchemeSchema,
  artifactSchema,
  authorizationCodeOAuthFlowSchema,
  clientCredentialsOAuthFlowSchema,
  dataPartSchema,
  filePartSchema,
  fileWithBytesSchema,
  fileWithUriSchema,
  httpAuthSecuritySchemeSchema,
  implicitOAuthFlowSchema,
  messageSchema,
  mutualTlsSecuritySchemeSchema,
  oAuth2SecuritySchemeSchema,
  oAuthFlowsSchema,
  openIdConnectSecuritySchemeSchema,
  partSchema,
  passwordOAuthFlowSchema,
  securitySchemeSchema,
  taskArtifactUpdateEventSchema,
  taskSchema,
  taskStatusSchema,
  taskStatusUpdateEventSchema,
  textPartSchema,
} from './schemas';

export type AgentInterface = z.infer<typeof agentInterfaceSchema>;

export type AgentExtension = z.infer<typeof agentExtensionSchema>;

export type AgentCapabilities = z.infer<typeof agentCapabilitiesSchema>;

export type AgentProvider = z.infer<typeof agentProviderSchema>;

export type AgentCardSignature = z.infer<typeof agentCardSignatureSchema>;

export type AgentSkill = z.infer<typeof agentSkillSchema>;

export type AuthorizationCodeOAuthFlow = z.infer<typeof authorizationCodeOAuthFlowSchema>;
export type ClientCredentialsOAuthFlow = z.infer<typeof clientCredentialsOAuthFlowSchema>;
export type ImplicitOAuthFlow = z.infer<typeof implicitOAuthFlowSchema>;
export type PasswordOAuthFlow = z.infer<typeof passwordOAuthFlowSchema>;

export type OAuthFlows = z.infer<typeof oAuthFlowsSchema>;

export type APIKeySecurityScheme = z.infer<typeof apiKeySecuritySchemeSchema>;
export type HTTPAuthSecurityScheme = z.infer<typeof httpAuthSecuritySchemeSchema>;
export type OAuth2SecurityScheme = z.infer<typeof oAuth2SecuritySchemeSchema>;
export type OpenIdConnectSecurityScheme = z.infer<typeof openIdConnectSecuritySchemeSchema>;
export type MutualTLSSecurityScheme = z.infer<typeof mutualTlsSecuritySchemeSchema>;

export type SecurityScheme = z.infer<typeof securitySchemeSchema>;

export type AgentCard = z.infer<typeof agentCardSchema>;

export type TextPart = z.infer<typeof textPartSchema>;

export type FileWithBytes = z.infer<typeof fileWithBytesSchema>;

export type FileWithUri = z.infer<typeof fileWithUriSchema>;

export type FilePart = z.infer<typeof filePartSchema>;

export type DataPart = z.infer<typeof dataPartSchema>;

export type Part = z.infer<typeof partSchema>;

export type Artifact = z.infer<typeof artifactSchema>;

export type Message = z.infer<typeof messageSchema>;

export type TaskStatus = z.infer<typeof taskStatusSchema>;

export type TaskStatusUpdateEvent = z.infer<typeof taskStatusUpdateEventSchema>;

export type Task = z.infer<typeof taskSchema>;

export type TaskArtifactUpdateEvent = z.infer<typeof taskArtifactUpdateEventSchema>;

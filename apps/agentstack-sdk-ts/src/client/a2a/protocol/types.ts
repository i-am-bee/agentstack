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
  authenticatedExtendedCardNotConfiguredErrorSchema,
  authorizationCodeOAuthFlowSchema,
  clientCredentialsOAuthFlowSchema,
  contentTypeNotSupportedErrorSchema,
  dataPartSchema,
  filePartSchema,
  fileWithBytesSchema,
  fileWithUriSchema,
  getTaskResponseSchema,
  getTaskSuccessResponseSchema,
  httpAuthSecuritySchemeSchema,
  implicitOAuthFlowSchema,
  internalErrorSchema,
  invalidAgentResponseErrorSchema,
  invalidParamsErrorSchema,
  invalidRequestErrorSchema,
  jsonParseErrorSchema,
  jsonRpcErrorResponseSchema,
  jsonRpcErrorSchema,
  messageSchema,
  methodNotFoundErrorSchema,
  mutualTlsSecuritySchemeSchema,
  oauth2SecuritySchemeSchema,
  oauthFlowsSchema,
  openIdConnectSecuritySchemeSchema,
  partSchema,
  passwordOAuthFlowSchema,
  pushNotificationNotSupportedErrorSchema,
  securitySchemeSchema,
  taskArtifactUpdateEventSchema,
  taskNotCancelableErrorSchema,
  taskNotFoundErrorSchema,
  taskSchema,
  taskStatusSchema,
  taskStatusUpdateEventSchema,
  textPartSchema,
  unsupportedOperationErrorSchema,
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

export type OAuthFlows = z.infer<typeof oauthFlowsSchema>;

export type APIKeySecurityScheme = z.infer<typeof apiKeySecuritySchemeSchema>;
export type HTTPAuthSecurityScheme = z.infer<typeof httpAuthSecuritySchemeSchema>;
export type OAuth2SecurityScheme = z.infer<typeof oauth2SecuritySchemeSchema>;
export type OpenIdConnectSecurityScheme = z.infer<typeof openIdConnectSecuritySchemeSchema>;
export type MutualTLSSecurityScheme = z.infer<typeof mutualTlsSecuritySchemeSchema>;

export type SecurityScheme = z.infer<typeof securitySchemeSchema>;

export type AgentCard = z.infer<typeof agentCardSchema>;

export type FileWithBytes = z.infer<typeof fileWithBytesSchema>;
export type FileWithUri = z.infer<typeof fileWithUriSchema>;

export type TextPart = z.infer<typeof textPartSchema>;
export type FilePart = z.infer<typeof filePartSchema>;
export type DataPart = z.infer<typeof dataPartSchema>;

export type Part = z.infer<typeof partSchema>;

export type Artifact = z.infer<typeof artifactSchema>;

export type Message = z.infer<typeof messageSchema>;

export type TaskStatus = z.infer<typeof taskStatusSchema>;

export type TaskStatusUpdateEvent = z.infer<typeof taskStatusUpdateEventSchema>;

export type Task = z.infer<typeof taskSchema>;

export type TaskArtifactUpdateEvent = z.infer<typeof taskArtifactUpdateEventSchema>;

export type JSONRPCError = z.infer<typeof jsonRpcErrorSchema>;
export type JSONParseError = z.infer<typeof jsonParseErrorSchema>;
export type InvalidRequestError = z.infer<typeof invalidRequestErrorSchema>;
export type MethodNotFoundError = z.infer<typeof methodNotFoundErrorSchema>;
export type InvalidParamsError = z.infer<typeof invalidParamsErrorSchema>;
export type InternalError = z.infer<typeof internalErrorSchema>;
export type TaskNotFoundError = z.infer<typeof taskNotFoundErrorSchema>;
export type TaskNotCancelableError = z.infer<typeof taskNotCancelableErrorSchema>;
export type PushNotificationNotSupportedError = z.infer<typeof pushNotificationNotSupportedErrorSchema>;
export type UnsupportedOperationError = z.infer<typeof unsupportedOperationErrorSchema>;
export type ContentTypeNotSupportedError = z.infer<typeof contentTypeNotSupportedErrorSchema>;
export type InvalidAgentResponseError = z.infer<typeof invalidAgentResponseErrorSchema>;
export type AuthenticatedExtendedCardNotConfiguredError = z.infer<
  typeof authenticatedExtendedCardNotConfiguredErrorSchema
>;

export type JSONRPCErrorResponse = z.infer<typeof jsonRpcErrorResponseSchema>;

export type GetTaskSuccessResponse = z.infer<typeof getTaskSuccessResponseSchema>;

export type GetTaskResponse = z.infer<typeof getTaskResponseSchema>;

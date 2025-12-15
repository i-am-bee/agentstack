/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type {
  AgentCapabilities,
  AgentCard,
  AgentCardSignature,
  AgentExtension,
  AgentInterface,
  AgentProvider,
  AgentSkill,
  APIKeySecurityScheme,
  Artifact,
  AuthorizationCodeOAuthFlow,
  ClientCredentialsOAuthFlow,
  DataPart,
  FilePart,
  FileWithBytes,
  FileWithUri,
  HTTPAuthSecurityScheme,
  ImplicitOAuthFlow,
  Message,
  MutualTLSSecurityScheme,
  OAuth2SecurityScheme,
  OAuthFlows,
  OpenIdConnectSecurityScheme,
  Part,
  PasswordOAuthFlow,
  SecurityScheme,
  Task,
  TaskArtifactUpdateEvent,
  TaskStatus,
  TaskStatusUpdateEvent,
  TextPart,
} from '@a2a-js/sdk';
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

type Equals<X, Y> = (<T>() => T extends X ? 1 : 2) extends <T>() => T extends Y ? 1 : 2 ? true : false;

type Assert<T extends true> = T;

// eslint-disable-next-line @typescript-eslint/no-unused-vars
type _ = {
  AgentCapabilities: Assert<Equals<z.infer<typeof agentCapabilitiesSchema>, AgentCapabilities>>;
  AgentCard: Assert<Equals<z.infer<typeof agentCardSchema>, AgentCard>>;
  AgentCardSignature: Assert<Equals<z.infer<typeof agentCardSignatureSchema>, AgentCardSignature>>;
  AgentExtension: Assert<Equals<z.infer<typeof agentExtensionSchema>, AgentExtension>>;
  AgentInterface: Assert<Equals<z.infer<typeof agentInterfaceSchema>, AgentInterface>>;
  AgentProvider: Assert<Equals<z.infer<typeof agentProviderSchema>, AgentProvider>>;
  AgentSkill: Assert<Equals<z.infer<typeof agentSkillSchema>, AgentSkill>>;
  ApiKeySecurityScheme: Assert<Equals<z.infer<typeof apiKeySecuritySchemeSchema>, APIKeySecurityScheme>>;
  Artifact: Assert<Equals<z.infer<typeof artifactSchema>, Artifact>>;
  AuthorizationCodeOAuthFlow: Assert<
    Equals<z.infer<typeof authorizationCodeOAuthFlowSchema>, AuthorizationCodeOAuthFlow>
  >;
  ClientCredentialsOAuthFlow: Assert<
    Equals<z.infer<typeof clientCredentialsOAuthFlowSchema>, ClientCredentialsOAuthFlow>
  >;
  DataPart: Assert<Equals<z.infer<typeof dataPartSchema>, DataPart>>;
  FilePart: Assert<Equals<z.infer<typeof filePartSchema>, FilePart>>;
  FileWithBytes: Assert<Equals<z.infer<typeof fileWithBytesSchema>, FileWithBytes>>;
  FileWithUri: Assert<Equals<z.infer<typeof fileWithUriSchema>, FileWithUri>>;
  HttpAuthSecurityScheme: Assert<Equals<z.infer<typeof httpAuthSecuritySchemeSchema>, HTTPAuthSecurityScheme>>;
  ImplicitOAuthFlow: Assert<Equals<z.infer<typeof implicitOAuthFlowSchema>, ImplicitOAuthFlow>>;
  Message: Assert<Equals<z.infer<typeof messageSchema>, Message>>;
  MutualTlsSecurityScheme: Assert<Equals<z.infer<typeof mutualTlsSecuritySchemeSchema>, MutualTLSSecurityScheme>>;
  OAuth2SecurityScheme: Assert<Equals<z.infer<typeof oAuth2SecuritySchemeSchema>, OAuth2SecurityScheme>>;
  OAuthFlows: Assert<Equals<z.infer<typeof oAuthFlowsSchema>, OAuthFlows>>;
  OpenIdConnectSecurityScheme: Assert<
    Equals<z.infer<typeof openIdConnectSecuritySchemeSchema>, OpenIdConnectSecurityScheme>
  >;
  Part: Assert<Equals<z.infer<typeof partSchema>, Part>>;
  PasswordOAuthFlow: Assert<Equals<z.infer<typeof passwordOAuthFlowSchema>, PasswordOAuthFlow>>;
  SecurityScheme: Assert<Equals<z.infer<typeof securitySchemeSchema>, SecurityScheme>>;
  Task: Assert<Equals<z.infer<typeof taskSchema>, Task>>;
  TaskArtifactUpdateEvent: Assert<Equals<z.infer<typeof taskArtifactUpdateEventSchema>, TaskArtifactUpdateEvent>>;
  TaskStatus: Assert<Equals<z.infer<typeof taskStatusSchema>, TaskStatus>>;
  TaskStatusUpdateEvent: Assert<Equals<z.infer<typeof taskStatusUpdateEventSchema>, TaskStatusUpdateEvent>>;
  TextPart: Assert<Equals<z.infer<typeof textPartSchema>, TextPart>>;
};

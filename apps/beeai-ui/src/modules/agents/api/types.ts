/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ApiPath, ApiResponse } from '#@types/utils.ts';

export type AgentsListResponse = ApiResponse<'/api/v1/acp/agents'>;

export type Agent = ApiResponse<'/api/v1/acp/agents/{name}'> & {
  input_content_types?: string[];
  metadata: {
    name?: string;
  };
};

export type AgentName = Agent['name'];

export type ReadAgentPath = ApiPath<'/api/v1/acp/agents/{name}'>;

export interface ListAgentsParams {
  onlyUiSupported?: boolean;
  sort?: boolean;
}

export enum UiType {
  Chat = 'chat',
  HandsOff = 'hands-off',
}

export enum LinkType {
  SourceCode = 'source-code',
  ContainerImage = 'container-image',
  Homepage = 'homepage',
  Documentation = 'documentation',
}

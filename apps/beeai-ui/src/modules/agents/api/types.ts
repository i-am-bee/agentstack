/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ApiPath, ApiResponse } from '#@types/utils.ts';

export type AgentsListResponse = ApiResponse<'/api/v1/acp/agents'>;

interface AgentToolInfo {
  name: string;
  description?: string;
}

export type Agent = ApiResponse<'/api/v1/acp/agents/{name}'> & {
  metadata: {
    name?: string;
    provider_id?: string;
    annotations?: {
      beeai_ui?: {
        ui_type: UiType;
        user_greeting?: string;
        display_name?: string;
        tools: AgentToolInfo[];
      };
    };
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

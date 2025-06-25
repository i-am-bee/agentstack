/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import type { ApiPath, ApiResponse } from '#@types/utils.ts';

export type AgentsListResponse = ApiResponse<'/api/v1/acp/agents'>;

export type Agent = ApiResponse<'/api/v1/acp/agents/{name}'> & {
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

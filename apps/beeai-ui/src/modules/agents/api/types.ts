/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { AgentManifest, Metadata } from 'acp-sdk';

export type { AgentName } from 'acp-sdk';

export type AgentMetadata = Metadata & { provider_id?: string };

export type Agent = Exclude<AgentManifest, 'metadata'> & { metadata?: AgentMetadata | null };

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

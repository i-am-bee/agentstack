/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Metadata } from 'acp-sdk';

import type { Provider } from '#modules/providers/api/types.ts';

export type AgentMetadata = Metadata & { provider_id?: string };

type AgentCard = Provider['agent_card'];
type AgentCardProvider = AgentCard['provider'];

export interface Agent extends Omit<AgentCard, 'provider'> {
  provider: Omit<Provider, 'agent_card'> & {
    metadata?: AgentCardProvider;
  };
  ui: UiExtensionParams;
}

export type AgentExtension = NonNullable<Agent['capabilities']['extensions']>[number];

export enum UiType {
  Chat = 'chat',
  HandsOff = 'hands-off',
}

export interface AgentTool {
  name: string;
  description: string;
}

export interface UiExtensionParams {
  ui_type?: UiType;
  user_greeting?: string;
  display_name: string;
  tools?: AgentTool[];

  // TODO: a2a added just for the sake of successful build
  avg_run_time_seconds?: string;
  avg_run_tokens?: string;
  framework?: string;
  license?: string;
  tags?: string[];
  documentation?: string;
  programming_language?: string;
}

export const AGENT_EXTENSION_UI_KEY = 'beeai_ui';
export interface UiExtension extends AgentExtension {
  uri: 'beeai_ui';
  params: UiExtensionParams & { [key: string]: unknown };
}

export enum LinkType {
  SourceCode = 'source-code',
  ContainerImage = 'container-image',
  Homepage = 'homepage',
  Documentation = 'documentation',
}

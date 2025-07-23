/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Provider } from '#modules/providers/api/types.ts';

type AgentCard = Provider['agent_card'];
type AgentCardProvider = AgentCard['provider'];

export interface Agent extends Omit<AgentCard, 'provider'> {
  provider: Omit<Provider, 'agent_card'> & {
    metadata?: AgentCardProvider;
  };
  ui: UIExtensionParams;
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

export interface UIExtensionParams {
  ui_type?: UiType;
  user_greeting?: string;
  display_name: string;
  tools?: AgentTool[];
  avg_run_time_seconds?: string;
  avg_run_tokens?: string;
  framework?: string;
  license?: string;
  tags?: string[];
  documentation?: string;
  programming_language?: string;
  links?: AgentLink[];
  author?: AgentAuthor;
  contributors?: AgentContributor[];
  prompt_suggestions?: string[];
}

export const AGENT_EXTENSION_UI_KEY = 'beeai_ui';
export interface UiExtension extends AgentExtension {
  uri: 'beeai_ui';
  params: UIExtensionParams & { [key: string]: unknown };
}

export enum AgentLinkType {
  SourceCode = 'source-code',
  ContainerImage = 'container-image',
  Homepage = 'homepage',
  Documentation = 'documentation',
}

export interface AgentLink {
  url: string;
  type: AgentLinkType;
}

export interface AgentAuthor {
  name: string;
  email?: string;
}

export interface AgentContributor extends AgentAuthor {
  name: string;
  email?: string;
  url?: string;
}

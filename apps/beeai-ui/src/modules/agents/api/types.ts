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

export enum SupportedUIType {
  Chat = 'chat',
  HandsOff = 'hands-off',
}

export interface AgentTool {
  name: string;
  description: string;
}

export interface UIExtensionParams {
  ui_type?: SupportedUIType | string;
  user_greeting?: string;
  tools?: AgentTool[];
  framework?: string;
  license?: string;
  programming_language?: string;
  homepage_url?: string;
  source_code_url?: string;
  container_image_url?: string;
  author?: AgentContributor;
  contributors?: AgentContributor[];
}

export const AGENT_EXTENSION_URI = 'https://a2a-extensions.beeai.dev/ui/agent-detail/v1';
export interface UiExtension extends AgentExtension {
  uri: typeof AGENT_EXTENSION_URI;
  params: UIExtensionParams & { [key: string]: unknown };
}

export interface AgentContributor {
  name: string;
  email?: string;
  url?: string;
}

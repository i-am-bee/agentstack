/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { AgentDetail, Provider } from 'agentstack-sdk';

type AgentCard = Provider['agent_card'];
type AgentCardProvider = AgentCard['provider'];

export interface Agent extends Omit<AgentCard, 'provider'> {
  provider: Omit<Provider, 'agent_card'> & {
    metadata?: AgentCardProvider;
  };
  ui: AgentDetail;
}

export type AgentExtension = NonNullable<Agent['capabilities']['extensions']>[number];

export enum ListAgentsOrderBy {
  Name = 'name',
  CreatedAt = 'created_at',
  LastActiveAt = 'last_active_at',
}

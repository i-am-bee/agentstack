/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import groupBy from 'lodash/groupBy';

import type { Agent } from '#modules/agents/api/types.ts';

export function groupAgentsByProvider(agents: Agent[] | undefined) {
  return groupBy(agents, (agent) => agent.provider.id);
}

export function isRecentlyUsedAgent(agent: Agent) {
  const {
    provider: { created_at: createdAt, last_active_at: lastActiveAt },
  } = agent;

  if (!createdAt || !lastActiveAt) {
    return false;
  }

  const diff = new Date(lastActiveAt).getTime() - new Date(createdAt).getTime();

  return diff > RECENT_THRESHOLD_MS;
}

const RECENT_THRESHOLD_MS = 1000 * 60; // 1 minute

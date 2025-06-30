/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import groupBy from 'lodash/groupBy';

import type { Agent } from '#modules/agents/api/types.ts';

export const groupAgentsByProvider = (agents: Agent[] | undefined) => {
  return groupBy(agents, (agent) => agent.metadata.provider_id);
};

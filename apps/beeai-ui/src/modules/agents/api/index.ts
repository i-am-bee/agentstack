/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { acp } from '#acp/index.ts';

import type { AgentName } from './types';

export async function listAgents() {
  return await acp.agents();
}

export async function readAgent(name: AgentName) {
  return await acp.agent(name);
}

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Part } from '@a2a-js/sdk';

import type { Agent } from '#modules/agents/api/types.ts';

export interface RunAgentParams {
  agent: Agent;
  parts: Part[];
}

export interface RunStats {
  startTime?: number;
  endTime?: number;
}

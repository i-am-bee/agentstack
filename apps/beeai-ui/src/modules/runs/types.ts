/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Agent } from '#modules/agents/api/types.ts';

import type { GenericEvent, MessagePart } from './api/types';

export enum Role {
  User = 'user',
  Agent = 'agent',
}

export interface RunAgentParams {
  agent: Agent;
  messageParts: MessagePart[];
}

export interface RunStats {
  startTime?: number;
  endTime?: number;
}

export type RunLog = GenericEvent['generic'];

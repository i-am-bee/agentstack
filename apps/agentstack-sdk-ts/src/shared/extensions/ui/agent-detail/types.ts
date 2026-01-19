/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type z from 'zod';

import type {
  agentDetailContributorSchema,
  agentDetailSchema,
  agentDetailToolSchema,
  agentDetailVariableSchema,
} from './schemas';

export enum InteractionMode {
  SingleTurn = 'single-turn',
  MultiTurn = 'multi-turn',
}

export type AgentDetailTool = z.infer<typeof agentDetailToolSchema>;

export type AgentDetailContributor = z.infer<typeof agentDetailContributorSchema>;

export type AgentDetailVariable = z.infer<typeof agentDetailVariableSchema>;

export type AgentDetail = z.infer<typeof agentDetailSchema>;

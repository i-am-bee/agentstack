/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use client';
import type { A2AClient } from '@a2a-js/sdk/client';
import { createContext } from 'react';

import type { Agent } from '#modules/agents/api/types.ts';

export const AgentClientContext = createContext<AgentClientContextValue | undefined>(undefined);

export interface AgentClientContextValue {
  agent: Agent;
  client: A2AClient;
}

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { use } from 'react';

import { AgentRunContext } from './agent-run-context';

export function useAgentRun() {
  const context = use(AgentRunContext);

  if (!context) {
    throw new Error('useAgentRun must be used within a AgentRunProvider');
  }

  return context;
}

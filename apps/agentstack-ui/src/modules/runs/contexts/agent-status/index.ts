/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { use } from 'react';

import { AgentStatusContext } from './agent-status-context';

export function useAgentStatus() {
  const context = use(AgentStatusContext);

  if (!context) {
    throw new Error('useAgentStatus must be used within a AgentStatusProvider');
  }

  return context;
}

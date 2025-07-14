/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { use } from 'react';

import { AgentClientContext } from './agent-client-context';

export function useAgentClient() {
  const context = use(AgentClientContext);

  if (!context) {
    throw new Error('useAgentClient must be used within a AgentClientProvider');
  }

  return context;
}

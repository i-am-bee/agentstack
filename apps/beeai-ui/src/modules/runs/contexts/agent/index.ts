/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { use } from 'react';

import { AgentContext } from './agent-context';

export function useAgent() {
  const context = use(AgentContext);

  if (!context) {
    throw new Error('useAgent must be used within a AgentProvider');
  }

  return context;
}

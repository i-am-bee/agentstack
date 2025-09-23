/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { use } from 'react';

import { AgentSecretsContext } from './agent-secrets-context';

export function useAgentSecrets() {
  const context = use(AgentSecretsContext);

  if (!context) {
    throw new Error('useAgentSecrets must be used within a AgentSecretsProvider');
  }

  return context;
}

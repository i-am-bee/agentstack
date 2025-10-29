/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { use } from 'react';

import { AgentSecretsContext } from './agent-secrets-context';

export function useAgentSecrets() {
  return use(AgentSecretsContext);
}

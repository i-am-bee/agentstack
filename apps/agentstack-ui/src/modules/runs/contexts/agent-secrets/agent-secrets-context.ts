/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use client';
import { createContext } from 'react';

import type { AgentSecret } from './types';

export const AgentSecretsContext = createContext<AgentSecretsContextValue>({
  demandedSecrets: [],
});

interface AgentSecretsContextValue {
  demandedSecrets: AgentSecret[];
}

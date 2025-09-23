/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use client';
import { createContext } from 'react';

import type { AgentRequestSecrets, AgentSecret } from './types';

export const AgentSecretsContext = createContext<AgentSecretsContextValue | undefined>(undefined);

interface AgentSecretsContextValue {
  secrets: AgentSecret[];
  getRequestSecrets: () => AgentRequestSecrets;
  updateSecret: (key: string, value: string) => void;
  revokeSecret: (key: string) => void;
  storeSecrets: (secrets: Record<string, string>) => void;
}

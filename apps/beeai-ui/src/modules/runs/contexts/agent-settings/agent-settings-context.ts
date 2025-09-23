/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use client';
import { createContext } from 'react';

import type { AgentRequestedApiKeys } from './types';

export const AgentSettingsContext = createContext<AgentSettingsContextValue | undefined>(undefined);

interface AgentSettingsContextValue {
  requestedApiKeys: AgentRequestedApiKeys;
  updateApiKey: (key: string, value: string) => void;
  revokeApiKey: (key: string) => void;
  provideSecrets: (secrets: Record<string, string>) => void;
}

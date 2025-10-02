/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use client';
import noop from 'lodash/noop';
import { createContext } from 'react';

import type { AgentRequestSecrets, AgentSecret } from './types';

export const AgentSecretsContext = createContext<AgentSecretsContextValue>({
  secrets: [],
  hasSeenModal: false,
  markModalAsSeen: noop,
  getRequestSecrets: () => ({}),
});

interface AgentSecretsContextValue {
  secrets: AgentSecret[];
  hasSeenModal: boolean;
  markModalAsSeen: () => void;
  getRequestSecrets: () => AgentRequestSecrets;
}

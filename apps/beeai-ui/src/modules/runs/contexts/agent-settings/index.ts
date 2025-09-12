/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { use } from 'react';

import { AgentSettingsContext } from './agent-settings-context';

export function useAgentSettings() {
  const context = use(AgentSettingsContext);

  if (!context) {
    throw new Error('useAgentSettings must be used within a AgentSettingsProvider');
  }

  return context;
}

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { createContext } from 'react';

import type { Fulfillments } from '#api/a2a/types.ts';
import type { ContextId } from '#modules/tasks/api/types.ts';

interface PlatformContextValue {
  contextId: ContextId | null;
  matchedProviders?: Record<string, string[]>;
  selectedProviders: Record<string, string>;
  getContextId: () => ContextId;
  resetContext: () => void;
  getPlatformToken: () => Promise<string>;
  getFullfilments: () => Promise<Fulfillments>;
  selectProvider: (key: string, value: string) => void;
  selectMCPServer: (key: string, value: string) => void;
  selectedMCPServers: Record<string, string>;
}

export const PlatformContext = createContext<PlatformContextValue | null>(null);

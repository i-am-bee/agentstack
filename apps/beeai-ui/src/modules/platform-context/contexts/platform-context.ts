/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { createContext } from 'react';

import type { Fulfillments } from '#api/a2a/types.ts';
import type { ContextId } from '#modules/tasks/api/types.ts';

interface PlatformContextValue {
  contextId: ContextId | null;
  getContextId: () => ContextId;
  resetContext: () => void;
  getPlatformToken: () => Promise<string>;
  getFullfilments: () => Promise<Fulfillments>;
  matchedProviders: Record<string, string[]> | undefined;
  selectProvider: (key: string, value: string) => void;
}

export const PlatformContext = createContext<PlatformContextValue | null>(null);

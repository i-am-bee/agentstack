/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { UseMutateAsyncFunction } from '@tanstack/react-query';
import type { Context, CreateContextRequest, ListContextHistoryResponse } from 'agentstack-sdk';
import { createContext } from 'react';

import type { Agent } from '#modules/agents/api/types.ts';
import type { ContextId } from '#modules/tasks/api/types.ts';

export type ContextToken = {
  token: string;
  expires_at: string | null;
};

interface PlatformContextValue {
  contextId: ContextId | null;
  history?: ListContextHistoryResponse;

  getContextId: () => ContextId;
  resetContext: () => void;
  createContext: UseMutateAsyncFunction<Context, Error, CreateContextRequest>;
  updateContextWithAgentMetadata: (agent: Agent) => Promise<void>;
}

export const PlatformContext = createContext<PlatformContextValue | null>(null);

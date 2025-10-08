/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { UseMutateAsyncFunction } from '@tanstack/react-query';
import { createContext } from 'react';

import type { Agent } from '#modules/agents/api/types.ts';
import type { ContextId } from '#modules/tasks/api/types.ts';

import type { CreateContextParams, CreateContextResponse, ListContextHistoryResponse } from '../api/types';

export type ContextToken = {
  token: string;
  expires_at: string | null;
};

interface PlatformContextValue {
  contextId: ContextId | null;
  history?: ListContextHistoryResponse;

  getContextId: () => ContextId;
  resetContext: () => void;
  createContext: UseMutateAsyncFunction<CreateContextResponse | undefined, Error, CreateContextParams>;
  updateContextWithAgentMetadata: (agent: Agent) => Promise<void>;
}

export const PlatformContext = createContext<PlatformContextValue | null>(null);

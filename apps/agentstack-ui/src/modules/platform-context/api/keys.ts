/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ListContextHistoryParams, ListContextsParams } from './types';

export const contextKeys = {
  all: () => ['contexts'] as const,
  lists: () => [...contextKeys.all(), 'list'] as const,
  list: ({ query = {} }: ListContextsParams) => [...contextKeys.lists(), query] as const,
  histories: () => [...contextKeys.all(), 'history'] as const,
  history: ({ contextId, query = {} }: ListContextHistoryParams) =>
    [...contextKeys.histories(), contextId, query] as const,
  historyInitial: ({ contextId, query = {} }: ListContextHistoryParams) =>
    [...contextKeys.history({ contextId }), 'initial', query] as const,
};

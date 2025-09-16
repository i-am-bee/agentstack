/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ListContextHistoryParams, ListContextsParams } from '../types';

export const contextKeys = {
  all: () => ['contexts'] as const,
  lists: () => [...contextKeys.all(), 'list'] as const,
  list: (params: ListContextsParams) => [...contextKeys.lists(), params.query] as const,
  histories: () => [...contextKeys.all(), 'history'] as const,
  history: (params: ListContextHistoryParams) => [...contextKeys.histories(), params.contextId, params.query] as const,
};

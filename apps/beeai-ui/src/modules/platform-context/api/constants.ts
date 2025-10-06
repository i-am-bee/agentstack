/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ListContextHistoryQuery, ListContextsQuery } from './types';

export const LIST_CONTEXTS_DEFAULT_QUERY: ListContextsQuery = { limit: 10, include_empty: false };

export const LIST_CONTEXT_HISTORY_DEFAULT_QUERY: ListContextHistoryQuery = { limit: 10 };

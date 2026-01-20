/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ListContextHistoryRequest, ListContextsRequest } from 'agentstack-sdk';

export const LIST_CONTEXTS_DEFAULT_QUERY: ListContextsRequest['query'] = { limit: 10, include_empty: false };

export const LIST_CONTEXT_HISTORY_DEFAULT_QUERY: ListContextHistoryRequest['query'] = { limit: 10 };

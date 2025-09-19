/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { createContext } from 'react';

import type { ListContextHistoryResponse } from '#modules/platform-context/api/types.ts';

export const HistoryContext = createContext<HistoryContextValue>({});

interface HistoryContextValue {
  contextId?: string;
  initialData?: ListContextHistoryResponse;
}

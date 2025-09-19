/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { type PropsWithChildren, useMemo } from 'react';

import type { ListContextHistoryResponse } from '#modules/platform-context/api/types.ts';

import { HistoryContext } from './history-context';

interface Props {
  contextId: string | undefined;
  initialData: ListContextHistoryResponse | undefined;
}

export function HistoryProvider({ contextId, initialData, children }: PropsWithChildren<Props>) {
  const contextValue = useMemo(
    () => ({
      contextId,
      initialData,
    }),
    [contextId, initialData],
  );

  return <HistoryContext.Provider value={contextValue}>{children}</HistoryContext.Provider>;
}

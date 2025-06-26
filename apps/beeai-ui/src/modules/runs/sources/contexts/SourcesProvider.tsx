/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { type PropsWithChildren, useEffect, useMemo, useState } from 'react';

import { useApp } from '#contexts/App/index.ts';

import type { SourcesData } from '../api/types';
import { SourcesContext } from './sources-context';
import type { ActiveMessageKey, ActiveSourceKey } from './types';

interface Props {
  sourcesData: SourcesData;
}

export function SourcesProvider({ sourcesData, children }: PropsWithChildren<Props>) {
  const { sourcesPanelOpen } = useApp();
  const [activeMessageKey, setActiveMessageKey] = useState<ActiveMessageKey>(null);
  const [activeSourceKey, setActiveSourceKey] = useState<ActiveSourceKey>(null);

  useEffect(() => {
    if (!sourcesPanelOpen) {
      setActiveSourceKey(null);
    }
  }, [sourcesPanelOpen]);

  const contextValue = useMemo(
    () => ({
      sourcesData,
      activeMessageKey,
      activeSourceKey,
      setActiveMessageKey,
      setActiveSourceKey,
    }),
    [sourcesData, activeMessageKey, activeSourceKey, setActiveMessageKey, setActiveSourceKey],
  );

  return <SourcesContext.Provider value={contextValue}>{children}</SourcesContext.Provider>;
}

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { type PropsWithChildren, useEffect, useMemo, useState } from 'react';

import { useApp } from '#contexts/App/index.ts';
import { SidePanelVariant } from '#contexts/App/types.ts';
import type { MessageSourcesMap } from '#modules/sources/types.ts';

import { SourcesContext } from './sources-context';
import type { ActiveSource } from './types';

interface Props {
  sources: MessageSourcesMap;
}

export function SourcesProvider({ sources, children }: PropsWithChildren<Props>) {
  const { activeSidePanel } = useApp();
  const [activeSource, setActiveSource] = useState<ActiveSource | null>(null);

  const isOpen = activeSidePanel === SidePanelVariant.Sources;

  useEffect(() => {
    if (!isOpen) {
      setActiveSource(null);
    }
  }, [isOpen]);

  const contextValue = useMemo(
    () => ({
      sources,
      activeSource,
      setActiveSource,
    }),
    [sources, activeSource, setActiveSource],
  );

  return <SourcesContext.Provider value={contextValue}>{children}</SourcesContext.Provider>;
}

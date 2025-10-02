/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use client';

import type { PropsWithChildren } from 'react';
import { useCallback, useMemo, useState } from 'react';

import { AppContext } from './app-context';
import type { RuntimeConfig, SidePanelVariant } from './types';

interface Props {
  config: RuntimeConfig;
}

export function AppProvider({ config, children }: PropsWithChildren<Props>) {
  const [navigationOpen, setNavigationOpen] = useState(false);
  const [closeNavOnClickOutside, setCloseNavOnClickOutside] = useState(false);
  const [activeSidePanel, setActiveSidePanel] = useState<SidePanelVariant | null>(null);

  const openSidePanel = useCallback((variant: SidePanelVariant) => {
    setActiveSidePanel(variant);
  }, []);

  const closeSidePanel = useCallback(() => {
    setActiveSidePanel(null);
  }, []);

  const contextValue = useMemo(
    () => ({
      config,
      navigationOpen,
      closeNavOnClickOutside,
      activeSidePanel,
      setNavigationOpen,
      setCloseNavOnClickOutside,
      openSidePanel,
      closeSidePanel,
    }),
    [config, navigationOpen, closeNavOnClickOutside, activeSidePanel, openSidePanel, closeSidePanel],
  );

  return <AppContext.Provider value={contextValue}>{children}</AppContext.Provider>;
}

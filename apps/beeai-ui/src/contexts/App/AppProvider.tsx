/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { PropsWithChildren } from 'react';
import { useCallback, useMemo, useState } from 'react';

import { AppContext } from './app-context';
import type { SidePanelVariant } from './types';

export function AppProvider({ children }: PropsWithChildren) {
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
      navigationOpen,
      closeNavOnClickOutside,
      activeSidePanel,
      setNavigationOpen,
      setCloseNavOnClickOutside,
      openSidePanel,
      closeSidePanel,
    }),
    [navigationOpen, closeNavOnClickOutside, activeSidePanel, openSidePanel, closeSidePanel],
  );

  return <AppContext.Provider value={contextValue}>{children}</AppContext.Provider>;
}

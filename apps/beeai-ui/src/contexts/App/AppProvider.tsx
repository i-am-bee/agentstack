/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { PropsWithChildren } from 'react';
import { useCallback, useMemo, useState } from 'react';

import { FeatureFlags } from '#utils/feature-flags.ts';

import { AppContext } from './app-context';
import type { SidePanelVariant } from './types';

interface Props {
  featureFlags: FeatureFlags;
}

export function AppProvider({ featureFlags, children }: PropsWithChildren<Props>) {
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
      featureFlags,
      navigationOpen,
      closeNavOnClickOutside,
      activeSidePanel,
      setNavigationOpen,
      setCloseNavOnClickOutside,
      openSidePanel,
      closeSidePanel,
    }),
    [featureFlags, navigationOpen, closeNavOnClickOutside, activeSidePanel, openSidePanel, closeSidePanel],
  );

  return <AppContext.Provider value={contextValue}>{children}</AppContext.Provider>;
}

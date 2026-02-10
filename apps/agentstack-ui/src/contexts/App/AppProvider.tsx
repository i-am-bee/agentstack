/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use client';
import type { PropsWithChildren } from 'react';
import { useState } from 'react';

import { AppContext } from './app-context';
import type { RuntimeConfig, SidePanelVariant } from './types';

interface Props {
  config: RuntimeConfig;
}

export function AppProvider({ config, children }: PropsWithChildren<Props>) {
  const [navbarOpen, setNavbarOpen] = useState(true);
  const [activeSidePanel, setActiveSidePanel] = useState<SidePanelVariant | null>(null);

  const openNavbar = () => {
    setNavbarOpen(true);
  };

  const closeNavbar = () => {
    setNavbarOpen(false);
  };

  const openSidePanel = (variant: SidePanelVariant) => {
    setActiveSidePanel(variant);
  };

  const closeSidePanel = () => {
    setActiveSidePanel(null);
  };

  const contextValue = {
    config,
    navbarOpen,
    activeSidePanel,
    openNavbar,
    closeNavbar,
    openSidePanel,
    closeSidePanel,
  };

  return <AppContext.Provider value={contextValue}>{children}</AppContext.Provider>;
}

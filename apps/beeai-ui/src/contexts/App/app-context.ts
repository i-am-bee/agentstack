/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { createContext, type Dispatch, type SetStateAction } from 'react';

import type { RuntimeConfig, SidePanelVariant } from './types';

export const AppContext = createContext<AppContextValue | undefined>(undefined);

interface AppContextValue {
  config: RuntimeConfig;
  sidebarOpen: boolean;
  closeSidebarOnClickOutside: boolean;
  activeSidePanel: SidePanelVariant | null;
  setSidebarOpen: Dispatch<SetStateAction<boolean>>;
  setCloseSidebarOnClickOutside: Dispatch<SetStateAction<boolean>>;
  openSidePanel: (variant: SidePanelVariant) => void;
  closeSidePanel: () => void;
}

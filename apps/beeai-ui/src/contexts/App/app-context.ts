/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { createContext, type Dispatch, type SetStateAction } from 'react';

import type { FeatureFlags } from '#utils/feature-flags.ts';

import type { SidePanelVariant } from './types';

export const AppContext = createContext<AppContextValue | undefined>(undefined);

interface AppContextValue {
  featureFlags: FeatureFlags;
  navigationOpen: boolean;
  closeNavOnClickOutside: boolean;
  activeSidePanel: SidePanelVariant | null;
  isAuthEnabled: boolean;
  setNavigationOpen: Dispatch<SetStateAction<boolean>>;
  setCloseNavOnClickOutside: Dispatch<SetStateAction<boolean>>;
  openSidePanel: (variant: SidePanelVariant) => void;
  closeSidePanel: () => void;
}

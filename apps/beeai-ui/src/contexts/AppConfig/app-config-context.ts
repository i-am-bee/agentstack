/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use client';

import { createContext } from 'react';

import { FeatureFlags } from '#utils/feature-flags.ts';

export const AppConfigContext = createContext<AppConfigContextValue>({} as AppConfigContextValue);

interface AppConfigContextValue {
  featureFlags: FeatureFlags;
}

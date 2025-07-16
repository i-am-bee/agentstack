/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use client';

import { createContext } from 'react';

import type { FeatureFlags } from './api/types';

export const AppConfigContext = createContext<AppConfigContextValue>({} as AppConfigContextValue);

interface AppConfigContextValue {
  featureFlags?: FeatureFlags;
}

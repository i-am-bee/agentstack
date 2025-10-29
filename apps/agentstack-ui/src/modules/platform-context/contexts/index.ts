/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { use } from 'react';

import { PlatformContext } from './platform-context';

export function usePlatformContext() {
  const context = use(PlatformContext);

  if (!context) {
    throw new Error('usePlatformContext must be used within a PlatformContextProvider');
  }

  return context;
}

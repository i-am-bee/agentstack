/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { use } from 'react';

import { AppContext } from './app-context';

export function useApp() {
  const context = use(AppContext);

  if (!context) {
    throw new Error('useApp must be used within a AppProvider');
  }

  return context;
}

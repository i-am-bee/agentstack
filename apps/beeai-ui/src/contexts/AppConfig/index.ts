/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { use } from 'react';

import { AppConfigContext } from './app-config-context';

export function useAppConfig() {
  const context = use(AppConfigContext);

  if (!context) {
    throw new Error('useAppConfig must be used within a AppConfigContext');
  }

  return context;
}

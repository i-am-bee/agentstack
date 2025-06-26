/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { use } from 'react';

import { SourcesContext } from './sources-context';

export function useSources() {
  const context = use(SourcesContext);

  if (!context) {
    throw new Error('useSources must be used within a SourcesProvider');
  }

  return context;
}

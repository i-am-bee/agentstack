/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { use } from 'react';

import { A2AClientContext } from './a2a-client-context';

export function useA2AClient() {
  const context = use(A2AClientContext);

  if (!context) {
    throw new Error('useA2AClient must be used within A2AClientProvider');
  }

  return context;
}

export { A2AClientProvider } from './A2AClientProvider';

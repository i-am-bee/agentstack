/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useContext } from 'react';

import { ComposeContext } from './compose-context';

export function useCompose() {
  const context = useContext(ComposeContext);

  if (!context) {
    throw new Error('useCompose must be used within ComposeProvider');
  }

  return context;
}

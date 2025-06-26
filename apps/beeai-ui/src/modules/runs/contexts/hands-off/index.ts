/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { use } from 'react';

import { HandsOffContext } from './hands-off-context';

export function useHandsOff() {
  const context = use(HandsOffContext);

  if (!context) {
    throw new Error('useHandsOff must be used within a HandsOffProvider');
  }

  return context;
}

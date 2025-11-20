/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
import { use } from 'react';

import { CanvasContext } from './canvas-context';

export function useCanvas() {
  const context = use(CanvasContext);

  if (!context) {
    throw new Error('useCanvas must be used within a CanvasProvider');
  }

  return context;
}

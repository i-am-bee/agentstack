/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { CSSProperties } from 'react';

export function createScrollbarStyles({ width }: { width: number }) {
  return {
    style: { '--scrollbar-width': `${width}px` } as CSSProperties,
  };
}

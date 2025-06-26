/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ReactNode } from 'react';

interface Props {
  count: number;
  render: (idx: number) => ReactNode;
}

export function SkeletonItems({ count, render }: Props) {
  return Array.from({ length: count }, (_, idx) => render(idx));
}

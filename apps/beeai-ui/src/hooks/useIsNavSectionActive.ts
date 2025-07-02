/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { usePathname } from 'next/navigation';
import { useCallback } from 'react';

import type { NavSectionName } from '#utils/router.ts';

export function useIsNavSectionActive() {
  const pathname = usePathname();
  const section = pathname?.split('/').at(1);

  return useCallback((name: NavSectionName) => name === section, [section]);
}

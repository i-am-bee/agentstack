/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useCallback } from 'react';
import { useLocation } from 'react-router';

import type { NavSectionName } from '#utils/router.ts';

export function useIsNavSectionActive() {
  const { pathname } = useLocation();
  const section = pathname.split('/').at(1);

  return useCallback((name: NavSectionName) => name === section, [section]);
}

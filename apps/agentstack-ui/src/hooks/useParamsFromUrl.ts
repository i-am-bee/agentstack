/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { usePathname } from 'next/navigation';

import { getRunParamsFromUrl } from '#modules/runs/utils.ts';

export function useParamsFromUrl() {
  const pathname = usePathname();

  return getRunParamsFromUrl(pathname);
}

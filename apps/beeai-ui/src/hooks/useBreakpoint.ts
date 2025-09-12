/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { breakpoints } from '@carbon/layout';
import { useMediaQuery } from 'usehooks-ts';

type Breakpoint = keyof typeof breakpoints;

export function useBreakpoint(breakpoint: Breakpoint) {
  const { width } = breakpoints[breakpoint];
  const matches = useMediaQuery(`(min-width: ${width})`);

  return matches;
}

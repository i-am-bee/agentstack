/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { moderate02, motion as carbonMotion } from '@carbon/motion';
import type { Variant } from 'framer-motion';

export function parseCarbonMotion(string: string): number[] {
  const matches = string.match(/-?\d*\.?\d+/g);

  return matches ? matches.map(Number) : [];
}

export function fadeProps({
  hidden,
  visible,
}: {
  hidden?: Variant;
  visible?: Variant;
} = {}) {
  return {
    variants: {
      hidden: {
        opacity: 0,
        transition: {
          duration: 0,
          ease: parseCarbonMotion(carbonMotion('exit', 'expressive')),
        },
        ...hidden,
      },
      visible: {
        opacity: 1,
        transition: {
          duration: parseFloat(moderate02) / 1000,
          ease: parseCarbonMotion(carbonMotion('entrance', 'expressive')),
        },
        ...visible,
      },
    },
    initial: 'hidden',
    animate: 'visible',
    exit: 'hidden',
  };
}

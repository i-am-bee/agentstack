/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { moderate02, motion as carbonMotion } from '@carbon/motion';
import type { Easing, Variant } from 'framer-motion';

export function parseCarbonMotion(string: string): Easing {
  const matches = string.match(/-?\d*\.?\d+/g);
  const definition = matches?.map(Number);

  return definition?.length === 4 ? (definition as [number, number, number, number]) : 'linear';
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

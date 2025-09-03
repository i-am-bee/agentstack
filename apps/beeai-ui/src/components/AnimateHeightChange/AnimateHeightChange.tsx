/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { moderate02, motion as carbonMotion } from '@carbon/motion';
import clsx from 'clsx';
import { motion } from 'framer-motion';
import type { PropsWithChildren } from 'react';
import { useEffect, useRef, useState } from 'react';

import { parseCarbonMotion } from '#utils/fadeProps.ts';

import classes from './AnimateHeightChange.module.scss';

interface Props {
  duration?: number;
  className?: string;
}

export function AnimateHeightChange({
  duration = parseFloat(moderate02) / 1000,
  className,
  children,
}: PropsWithChildren<Props>) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [height, setHeight] = useState<number | 'auto'>('auto');

  useEffect(() => {
    if (containerRef.current) {
      const resizeObserver = new ResizeObserver((entries) => {
        if (entries.length > 0) {
          const observedHeight = entries[0].contentRect.height;
          setHeight(observedHeight);
        }
      });

      resizeObserver.observe(containerRef.current);

      return () => {
        resizeObserver.disconnect();
      };
    }
  }, []);

  return (
    <motion.div
      className={clsx(classes.root, className)}
      style={{ height }}
      initial={{ height }}
      animate={{ height }}
      transition={{
        duration,
        ease: parseCarbonMotion(carbonMotion('entrance', 'expressive')),
      }}
    >
      <div ref={containerRef}>{children}</div>
    </motion.div>
  );
}

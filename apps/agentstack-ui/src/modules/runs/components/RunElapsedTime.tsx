/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import { useEffect, useState } from 'react';

import type { RunStats } from '../types';
import { runDuration } from '../utils';
import classes from './RunElapsedTime.module.scss';

interface Props {
  stats?: RunStats;
  className?: string;
}

export function RunElapsedTime({ stats, className }: Props) {
  const [now, setNow] = useState(Date.now());

  useEffect(() => {
    if (!stats?.startTime || stats.endTime) return;

    const interval = setInterval(() => {
      setNow(Date.now());
    }, 1000 / 24); // refresh at standard frame rate for smooth increments

    return () => clearInterval(interval);
  }, [stats]);

  if (!stats?.startTime) return null;

  const { startTime, endTime } = stats;
  const duration = runDuration((endTime || now) - startTime);

  return <span className={clsx(classes.root, className)}>{duration}</span>;
}

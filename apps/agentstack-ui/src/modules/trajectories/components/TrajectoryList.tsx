/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import { AnimatePresence, motion } from 'framer-motion';
import { useRef } from 'react';

import type { UITrajectoryPart } from '#modules/messages/types.ts';
import { fadeProps } from '#utils/fadeProps.ts';

import { TrajectoryItem } from './TrajectoryItem';
import classes from './TrajectoryList.module.scss';

interface Props {
  trajectories: UITrajectoryPart[];
  isOpen?: boolean;
}

export function TrajectoryList({ trajectories, isOpen }: Props) {
  const listRef = useRef<HTMLUListElement>(null);

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          {...fadeProps({
            visible: { height: 'auto' },
            hidden: { height: 0 },
          })}
          className={clsx(classes.root)}
        >
          <div className={classes.border} />
          <ul className={classes.list} ref={listRef}>
            {trajectories.map((trajectory) => (
              <li key={trajectory.id}>
                <TrajectoryItem trajectory={trajectory} />
              </li>
            ))}
          </ul>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

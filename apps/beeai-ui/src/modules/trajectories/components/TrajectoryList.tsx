/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { AnimatePresence, motion } from 'framer-motion';

import { useAutoScroll } from '#hooks/useAutoScroll.ts';
import type { UITrajectoryPart } from '#modules/messages/types.ts';
import { fadeProps } from '#utils/fadeProps.ts';

import { TrajectoryItem } from './TrajectoryItem';
import classes from './TrajectoryList.module.scss';

interface Props {
  trajectories: UITrajectoryPart[];
  isOpen?: boolean;
  autoScroll?: boolean;
}

export function TrajectoryList({ trajectories, isOpen, autoScroll }: Props) {
  const { ref: autoScrollRef } = useAutoScroll([trajectories.length]);

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div {...fadeProps()}>
          <ul className={classes.list}>
            {trajectories.map((trajectory) => (
              <li key={trajectory.id}>
                <TrajectoryItem trajectory={trajectory} />
              </li>
            ))}
          </ul>

          {autoScroll && <div ref={autoScrollRef} className={classes.bottom} />}
        </motion.div>
      )}
    </AnimatePresence>
  );
}

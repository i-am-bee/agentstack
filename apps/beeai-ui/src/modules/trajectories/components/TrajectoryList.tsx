/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { AnimatePresence, motion } from 'framer-motion';

import type { UITrajectoryPart } from '#modules/messages/types.ts';
import { fadeProps } from '#utils/fadeProps.ts';

import { TrajectoryItem } from './TrajectoryItem';

interface Props {
  trajectories: UITrajectoryPart[];
  isOpen?: boolean;
}

export function TrajectoryList({ trajectories, isOpen }: Props) {
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div {...fadeProps()}>
          <ul>
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

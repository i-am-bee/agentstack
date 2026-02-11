/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import { AnimatePresence, motion } from 'framer-motion';
import { useEffect, useState } from 'react';

import { usePrevious } from '#hooks/usePrevious.ts';
import type { UITrajectoryPart } from '#modules/messages/types.ts';
import { fadeProps } from '#utils/fadeProps.ts';

import { TrajectoryItem } from './TrajectoryItem';
import classes from './TrajectoryList.module.scss';

interface Props {
  trajectories: UITrajectoryPart[];
  isOpen?: boolean;
  isPending?: boolean;
}

export function TrajectoryList({ trajectories, isOpen, isPending }: Props) {
  const [canClampContent, setCanClampContent] = useState(!isPending);

  const previouslyOpen = usePrevious(isOpen);
  useEffect(() => {
    // Re-enable clamping when closed while no longer pending - ensuring trajectories
    // are not clamped when pending, or on first open after being in pending state
    if (previouslyOpen && !isOpen && !isPending) {
      setCanClampContent(true);
    }
  }, [isOpen, isPending, previouslyOpen]);

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
          <ul className={classes.list}>
            {trajectories.map((trajectory) => (
              <li key={trajectory.id}>
                <TrajectoryItem trajectory={trajectory} isPending={isPending} canClampContent={canClampContent} />
              </li>
            ))}
          </ul>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

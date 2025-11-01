/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import { AnimatePresence, motion } from 'framer-motion';
import { useEffect, useRef, useState } from 'react';

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
  const { ref: autoScrollRef } = useAutoScroll<HTMLLIElement>([trajectories.length], { duration: AUTOSCROLL_DURATION });
  const listRef = useRef<HTMLUListElement>(null);
  const [listHeight, setListHeight] = useState<number>(0);

  useEffect(() => {
    if (!autoScroll || !listRef.current) {
      return;
    }

    const updateHeight = () => {
      setListHeight(listRef.current?.offsetHeight ?? 0);
    };

    updateHeight();

    const resizeObserver = new ResizeObserver(updateHeight);
    resizeObserver.observe(listRef.current);

    return () => resizeObserver.disconnect();
  }, [autoScroll, trajectories.length]);

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          {...fadeProps({
            visible: { height: 'auto' },
            hidden: { height: 0 },
          })}
          className={clsx(classes.root, { [classes.autoScroll]: autoScroll })}
        >
          <div className={classes.inner}>
            <div className={classes.border} style={{ blockSize: autoScroll ? `${listHeight}px` : undefined }} />
            <ul className={classes.list} ref={listRef}>
              {trajectories.map((trajectory) => (
                <li key={trajectory.id}>
                  <TrajectoryItem trajectory={trajectory} />
                </li>
              ))}

              {autoScroll && <li ref={autoScrollRef} className={classes.scrollGuard}></li>}
            </ul>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

const AUTOSCROLL_DURATION = 1.4;

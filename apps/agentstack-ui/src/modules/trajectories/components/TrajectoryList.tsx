/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import clsx from 'clsx';
import { AnimatePresence, motion } from 'framer-motion';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { usePrevious } from '#hooks/usePrevious.ts';
import type { UITrajectoryPart } from '#modules/messages/types.ts';
import { fadeProps } from '#utils/fadeProps.ts';

import { AnimationStatus } from '../hooks/useAnimatedText';
import { TrajectoryItem } from './TrajectoryItem';
import classes from './TrajectoryList.module.scss';

export interface AnimatedTrajectory extends UITrajectoryPart {
  status: AnimationStatus;
  duration?: number;
}

interface Props {
  trajectories: UITrajectoryPart[];
  isOpen?: boolean;
  isPending?: boolean;
}

export function TrajectoryList({ trajectories, isOpen, isPending }: Props) {
  const [canClampContent, setCanClampContent] = useState(!isPending);
  const [animatedDoneTrajectoryIds, setAnimatedDoneTrajectoryIds] = useState<Set<string>>(new Set());

  const previouslyOpen = usePrevious(isOpen);
  useEffect(() => {
    if (previouslyOpen && !isOpen && !isPending) {
      setCanClampContent(true);
    }
  }, [isOpen, isPending, previouslyOpen]);

  const handleAnimationEnd = useCallback((trajectoryId: string) => {
    setAnimatedDoneTrajectoryIds((prev) => {
      const newIds = new Set(prev);
      newIds.add(trajectoryId);
      return newIds;
    });
  }, []);

  const animatedTrajectories: AnimatedTrajectory[] = useMemo(() => {
    const animatedTrajectories: AnimatedTrajectory[] = [];
    let animatingTrajectoryIdx: number | null = null;
    for (const [index, trajectory] of trajectories.entries()) {
      if (!isPending) {
        animatedTrajectories.push({
          ...trajectory,
          status: AnimationStatus.Completed,
        });
        continue;
      }

      if (animatingTrajectoryIdx !== null) {
        continue;
      }

      const wasAnimated = animatedDoneTrajectoryIds.has(trajectory.id);
      const isExpired = !trajectory.createdAt || Date.now() - trajectory.createdAt > SKIP_ANIMATION_THRESHOLD_MS;

      if (wasAnimated || isExpired) {
        animatedTrajectories.push({
          ...trajectory,
          status: AnimationStatus.Completed,
        });
        continue;
      }

      const pendingCount = trajectories.length - index;
      const durationMs = BASE_ANIMATION_DURATION_MS / pendingCount;

      animatedTrajectories.push({
        ...trajectory,
        status: AnimationStatus.Animating,
        duration: durationMs,
      });

      animatingTrajectoryIdx = index;
    }

    return animatedTrajectories;
  }, [animatedDoneTrajectoryIds, isPending, trajectories]);

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
            {animatedTrajectories.map((trajectory) => (
              <li key={trajectory.id}>
                <TrajectoryItem
                  trajectory={trajectory}
                  isPending={isPending}
                  canClampContent={canClampContent}
                  animateStatus={trajectory.status}
                  onAnimationEnd={() => handleAnimationEnd(trajectory.id)}
                />
              </li>
            ))}
          </ul>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

const BASE_ANIMATION_DURATION_MS = 1500;
const SKIP_ANIMATION_THRESHOLD_MS = 3000;

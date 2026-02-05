/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
import { useCallback, useEffect, useRef, useState } from 'react';

import type { UITrajectoryPart } from '#modules/messages/types.ts';

const MIN_TRAJECTORY_DISPLAY_MS = 2000;

interface UseCurrentTrajectoryOptions {
  trajectories: UITrajectoryPart[];
  isPending?: boolean;
}

export function useCurrentTrajectory({ trajectories, isPending }: UseCurrentTrajectoryOptions) {
  const [currentTrajectory, setCurrentTrajectory] = useState<UITrajectoryPart | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastUpdatedAtRef = useRef<number>(0);

  const clearCurrentTrajectoryTimeout = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  const scheduleTrajectoryUpdate = useCallback(
    (trajectory: UITrajectoryPart, delayMs: number) => {
      clearCurrentTrajectoryTimeout();

      timeoutRef.current = setTimeout(() => {
        setCurrentTrajectory(trajectory);
        lastUpdatedAtRef.current = Date.now();
        timeoutRef.current = null;
      }, delayMs);
    },
    [clearCurrentTrajectoryTimeout],
  );

  useEffect(() => {
    const latestTrajectory = trajectories.at(-1);
    if (!isPending || !latestTrajectory) {
      setCurrentTrajectory(null);
      lastUpdatedAtRef.current = 0;
      clearCurrentTrajectoryTimeout();
      return;
    }

    const now = Date.now();
    const timeSinceLastUpdate = now - lastUpdatedAtRef.current;
    const remainingDisplayTime = Math.max(0, MIN_TRAJECTORY_DISPLAY_MS - timeSinceLastUpdate);

    if (remainingDisplayTime === 0) {
      // Minimum display time has passed, show the new trajectory immediately
      setCurrentTrajectory(latestTrajectory);
      lastUpdatedAtRef.current = now;
    } else {
      // Schedule update after the remaining display time
      scheduleTrajectoryUpdate(latestTrajectory, remainingDisplayTime);
    }
  }, [clearCurrentTrajectoryTimeout, isPending, scheduleTrajectoryUpdate, trajectories]);

  useEffect(() => {
    return () => {
      clearCurrentTrajectoryTimeout();
    };
  }, [clearCurrentTrajectoryTimeout]);

  return currentTrajectory;
}

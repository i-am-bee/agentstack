/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use client';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { Spinner } from '#components/Spinner/Spinner.tsx';
import type { UITrajectoryPart } from '#modules/messages/types.ts';
import { hasViewableTrajectoryParts } from '#modules/trajectories/utils.ts';

import { TrajectoryButton } from './TrajectoryButton';
import { TrajectoryList } from './TrajectoryList';
import classes from './TrajectoryView.module.scss';

interface Props {
  trajectories: UITrajectoryPart[];
  isPending?: boolean;
}

export function TrajectoryView({ trajectories, isPending }: Props) {
  const [isOpen, setIsOpen] = useState(false);
  const [currentTrajectory, setCurrentTrajectory] = useState<UITrajectoryPart | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastTrajectoryRef = useRef<UITrajectoryPart | null>(null);

  const filteredTrajectories = useMemo(() => trajectories.filter(hasViewableTrajectoryParts), [trajectories]);
  const hasTrajectories = filteredTrajectories.length > 0;

  const groupedTrajectories = useMemo(() => {
    if (!hasTrajectories) {
      return [];
    }

    const groupMap = new Map<string, UITrajectoryPart>();
    filteredTrajectories.forEach((item) => {
      if (item.groupId) {
        const existingTrajectory = groupMap.get(item.groupId);
        groupMap.set(
          item.groupId,
          !existingTrajectory
            ? item
            : {
                ...existingTrajectory,
                title: item.title ?? existingTrajectory?.title,
                content: item.content ?? existingTrajectory?.content,
              },
        );
      }
    });

    const addedGroupIds = new Set<string>();
    const grouped: UITrajectoryPart[] = [];
    filteredTrajectories.forEach((item) => {
      if (item.groupId) {
        if (!addedGroupIds.has(item.groupId)) {
          grouped.push(groupMap.get(item.groupId)!);
          addedGroupIds.add(item.groupId);
        }
      } else {
        grouped.push(item);
      }
    });

    return grouped;
  }, [filteredTrajectories, hasTrajectories]);

  const clearCurrentTrajectoryTimeout = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  lastTrajectoryRef.current = groupedTrajectories.at(-1) ?? null;

  const updateCurrentTrajectory = useCallback(() => {
    const lastTrajectory = lastTrajectoryRef.current;
    console.log({ timeout: timeoutRef.current });

    if (timeoutRef.current !== null || !lastTrajectory) {
      return;
    }

    console.log('updateCurrentTrajectory', lastTrajectory);

    setCurrentTrajectory(lastTrajectory);
    timeoutRef.current = setTimeout(() => {
      timeoutRef.current = null;
      updateCurrentTrajectory();
    }, HEADER_UPDATE_DELAY_MS);
  }, []);

  useEffect(() => {
    if (isPending && groupedTrajectories.length) {
      updateCurrentTrajectory();
    } else {
      setCurrentTrajectory(null);
      clearCurrentTrajectoryTimeout();
    }
  }, [clearCurrentTrajectoryTimeout, groupedTrajectories.length, isPending, updateCurrentTrajectory]);

  useEffect(() => {
    return () => {
      clearCurrentTrajectoryTimeout();
    };
  }, [clearCurrentTrajectoryTimeout]);

  if (!hasTrajectories) {
    return null;
  }

  return (
    <div className={classes.root}>
      <div className={classes.header}>
        <TrajectoryButton
          isOpen={isOpen}
          onClick={() => setIsOpen((state) => !state)}
          message={currentTrajectory && !isOpen ? currentTrajectory.title || currentTrajectory.content : undefined}
        />
        {isPending && <Spinner center />}
      </div>
      <TrajectoryList trajectories={groupedTrajectories} isOpen={isOpen} />
    </div>
  );
}

const HEADER_UPDATE_DELAY_MS = 2000;

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use client';
import { useMemo, useState } from 'react';

import type { UITrajectoryPart } from '#modules/messages/types.ts';
import { hasViewableTrajectoryParts } from '#modules/trajectories/utils.ts';

import { TrajectoryButton } from './TrajectoryButton';
import { TrajectoryList } from './TrajectoryList';
import classes from './TrajectoryView.module.scss';

interface Props {
  trajectories: UITrajectoryPart[];
  toggleable?: boolean;
  autoScroll?: boolean;
}

export function TrajectoryView({ trajectories, toggleable, autoScroll }: Props) {
  const [isOpen, setIsOpen] = useState(false);

  const filteredTrajectories = trajectories.filter(hasViewableTrajectoryParts);
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

  if (!hasTrajectories) {
    return null;
  }

  return (
    <div className={classes.root}>
      {toggleable && <TrajectoryButton isOpen={isOpen} onClick={() => setIsOpen((state) => !state)} />}

      <TrajectoryList trajectories={groupedTrajectories} autoScroll={autoScroll} isOpen={toggleable ? isOpen : true} />
    </div>
  );
}

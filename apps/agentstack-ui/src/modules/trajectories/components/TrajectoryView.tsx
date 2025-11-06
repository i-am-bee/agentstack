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

    return filteredTrajectories.reduce((result: UITrajectoryPart[], trajectory) => {
      const { groupId } = trajectory;

      if (groupId && result.some((item) => item.groupId === groupId)) return result;

      if (groupId) {
        const groupedTrajectory = filteredTrajectories
          .filter((item) => item.groupId === groupId && trajectory.id !== item.id)
          .reduce(
            (grouped: UITrajectoryPart, { title, content }) => ({
              ...grouped,
              title: title ?? grouped.title,
              content: content ? [...(grouped.content ?? []), ...content] : grouped.content,
            }),
            trajectory,
          );

        result.push(groupedTrajectory);
      } else {
        result.push(trajectory);
      }

      return result;
    }, []);
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

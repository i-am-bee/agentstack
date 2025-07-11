/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState } from 'react';

import { useAutoScroll } from '#hooks/useAutoScroll.ts';
import type { TrajectoryMetadata } from '#modules/runs/api/types.ts';

import { hasViewableTrajectoryMetadata } from '../utils';
import { TrajectoryButton } from './TrajectoryButton';
import { TrajectoryList } from './TrajectoryList';
import classes from './TrajectoryView.module.scss';

interface Props {
  trajectories: TrajectoryMetadata[];
  toggleable?: boolean;
  autoScroll?: boolean;
}

export function TrajectoryView({ trajectories, toggleable, autoScroll }: Props) {
  const { ref: autoScrollRef } = useAutoScroll([trajectories.length]);
  const [isOpen, setIsOpen] = useState(false);

  const filteredTrajectories = trajectories.filter(hasViewableTrajectoryMetadata);
  const hasTrajectories = filteredTrajectories.length > 0;

  return hasTrajectories ? (
    <div className={classes.root}>
      {toggleable && <TrajectoryButton isOpen={isOpen} onClick={() => setIsOpen((state) => !state)} />}

      <TrajectoryList trajectories={filteredTrajectories} isOpen={toggleable ? isOpen : true} />

      {autoScroll && <div ref={autoScrollRef} className={classes.bottom} />}
    </div>
  ) : null;
}

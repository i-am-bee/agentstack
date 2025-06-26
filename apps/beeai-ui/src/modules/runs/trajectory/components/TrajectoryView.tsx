/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState } from 'react';

import type { TrajectoryMetadata } from '#modules/runs/api/types.ts';

import { hasViewableTrajectoryMetadata } from '../utils';
import { TrajectoryButton } from './TrajectoryButton';
import { TrajectoryList } from './TrajectoryList';
import classes from './TrajectoryView.module.scss';

interface Props {
  trajectories: TrajectoryMetadata[];
}

export function TrajectoryView({ trajectories }: Props) {
  const [isOpen, setIsOpen] = useState(false);

  const filteredTrajectories = trajectories.filter(hasViewableTrajectoryMetadata);
  const hasTrajectories = filteredTrajectories.length > 0;

  return hasTrajectories ? (
    <div className={classes.root}>
      <TrajectoryButton isOpen={isOpen} onClick={() => setIsOpen((state) => !state)} />

      <TrajectoryList trajectories={filteredTrajectories} isOpen={isOpen} />
    </div>
  ) : null;
}

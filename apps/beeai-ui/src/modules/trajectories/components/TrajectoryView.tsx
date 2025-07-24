/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use client';

import { useState } from 'react';

import { useAutoScroll } from '#hooks/useAutoScroll.ts';
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
  const { ref: autoScrollRef } = useAutoScroll([trajectories.length]);
  const [isOpen, setIsOpen] = useState(false);

  const filteredTrajectories = trajectories.filter(hasViewableTrajectoryParts);
  const hasTrajectories = filteredTrajectories.length > 0;

  if (!hasTrajectories) {
    return null;
  }

  return (
    <div className={classes.root}>
      {toggleable && <TrajectoryButton isOpen={isOpen} onClick={() => setIsOpen((state) => !state)} />}

      <TrajectoryList trajectories={filteredTrajectories} isOpen={toggleable ? isOpen : true} />

      {autoScroll && <div ref={autoScrollRef} className={classes.bottom} />}
    </div>
  );
}

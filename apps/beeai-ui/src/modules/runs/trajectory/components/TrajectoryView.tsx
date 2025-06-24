/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
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

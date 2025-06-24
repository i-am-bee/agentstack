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

import { AnimatePresence, motion } from 'framer-motion';

import type { TrajectoryMetadata } from '#modules/runs/api/types.ts';
import { fadeProps } from '#utils/fadeProps.ts';

import { TrajectoryItem } from './TrajectoryItem';

interface Props {
  trajectories: TrajectoryMetadata[];
  isOpen?: boolean;
}

export function TrajectoryList({ trajectories, isOpen }: Props) {
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div {...fadeProps()}>
          <ul>
            {trajectories.map((trajectory) => (
              <li key={trajectory.key}>
                <TrajectoryItem trajectory={trajectory} />
              </li>
            ))}
          </ul>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

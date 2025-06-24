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

import { isNotNull } from '#utils/helpers.ts';

import type { TrajectoryMetadata } from '../api/types';

export function hasViewableTrajectoryMetadata(trajectory: TrajectoryMetadata) {
  const nonViewableProperties = ['kind', 'key'] as NonViewableProperty[];

  return Object.entries(trajectory)
    .filter(([key]) => !nonViewableProperties.includes(key as NonViewableProperty))
    .some(([, value]) => isNotNull(value));
}

type NonViewableProperty = keyof Pick<TrajectoryMetadata, 'kind' | 'key'>;

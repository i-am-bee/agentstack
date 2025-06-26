/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
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

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { UITrajectoryPart } from '#modules/messages/types.ts';
import { isNotNull } from '#utils/helpers.ts';

import { NON_VIEWABLE_TRAJECTORY_PROPERTIES } from './constants';
import type { NonViewableTrajectoryProperty } from './types';

export function hasViewableTrajectoryParts(trajectory: UITrajectoryPart) {
  return Object.entries(trajectory)
    .filter(([key]) => !NON_VIEWABLE_TRAJECTORY_PROPERTIES.includes(key as NonViewableTrajectoryProperty))
    .some(([, value]) => isNotNull(value));
}

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { UITrajectoryPart } from '#modules/messages/types.ts';

export type NonViewableTrajectoryProperty = keyof Pick<UITrajectoryPart, 'kind' | 'id'>;

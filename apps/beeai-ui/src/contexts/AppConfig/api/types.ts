/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ApiResponse } from '#@types/utils.ts';

export type FeatureFlags = ApiResponse<'/api/v1/ui/config', 'get'>;
export type FeatureName = keyof FeatureFlags;

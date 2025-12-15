/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type z from 'zod';

import type { canvasEditRequestSchema } from './schemas';

export type CanvasEditRequest = z.infer<typeof canvasEditRequestSchema>;

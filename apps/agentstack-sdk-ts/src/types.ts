/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

export const interactionModeSchema = z.enum(['single-turn', 'multi-turn']);
export type InteractionMode = z.infer<typeof interactionModeSchema>;

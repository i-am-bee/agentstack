/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

export const canvasEditRequestSchema = z.object({
  start_index: z.int(),
  end_index: z.int(),
  description: z.string().nullish(),
  artifact_id: z.string(),
});

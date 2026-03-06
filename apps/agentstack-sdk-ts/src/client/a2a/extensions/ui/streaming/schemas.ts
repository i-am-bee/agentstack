/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

import { partSchema } from '../../../protocol/schemas';

export const streamingMessageSchema = z.object({
  message_id: z.string(),
  parts: z.array(partSchema),
  role: z.string(),
  metadata: z.record(z.string(), z.unknown()).nullish(),
});

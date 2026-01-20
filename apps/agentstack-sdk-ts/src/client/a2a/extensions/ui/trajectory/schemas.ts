/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

export const trajectoryMetadataSchema = z.object({
  title: z.string().nullish(),
  content: z.string().nullish(),
  group_id: z.string().nullish(),
});

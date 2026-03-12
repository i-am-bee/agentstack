/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

export const configSchema = z.object({
  platformUrl: z.string().default('http://agentstack-api.localtest.me:8080'),
  productionMode: z
    .string()
    .optional()
    .transform((value) => value?.toLowerCase() === 'true' || value === '1')
    .default(false),
});

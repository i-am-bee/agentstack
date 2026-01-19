/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { z } from 'zod';

const booleanFromEnv = z
  .string()
  .optional()
  .transform((val) => val?.toLowerCase() === 'true' || val === '1')
  .default(false);

const configSchema = z.object({
  platformUrl: z.string().default('http://127.0.0.1:8333'),
  productionMode: booleanFromEnv,
});

export type Config = z.infer<typeof configSchema>;

export function loadConfig(): Config {
  return configSchema.parse({
    platformUrl: process.env.PLATFORM_URL,
    productionMode: process.env.PRODUCTION_MODE,
  });
}

export function isProductionMode(): boolean {
  return loadConfig().productionMode;
}

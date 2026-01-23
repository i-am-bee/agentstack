/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { configSchema } from './schemas';

export function loadConfig() {
  return configSchema.parse({
    platformUrl: process.env.PLATFORM_URL,
    productionMode: process.env.PRODUCTION_MODE,
  });
}

export function isProductionMode() {
  return loadConfig().productionMode;
}

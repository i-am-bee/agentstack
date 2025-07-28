/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { z } from 'zod';

export interface A2AExtension<T extends string, D> {
  getSchema: () => z.ZodSchema<Partial<Record<T, D>>>;
  getKey: () => T;
}

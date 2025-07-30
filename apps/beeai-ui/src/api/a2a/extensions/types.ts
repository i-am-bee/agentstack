/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { z } from 'zod';

export interface A2AExtension<U extends string, D> {
  getSchema: () => z.ZodSchema<Partial<Record<U, D>>>;
  getUri: () => U;
}

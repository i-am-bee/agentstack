/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

export function a2aSchema<T extends z.ZodType>(schema: T) {
  return z.preprocess((value) => normalizeOptionalNulls(schema, value), schema);
}

// Only handles ZodOptional and ZodObject here.
// ZodArray/ZodUnion/ZodRecord aren't traversed and are normalized via their nested a2aSchema types (e.g., z.array(a2aSchema(...)).
function normalizeOptionalNulls(schema: z.core.$ZodType, data: unknown): unknown {
  if (schema instanceof z.ZodOptional) {
    if (data === null) {
      return undefined;
    }

    return normalizeOptionalNulls(schema.unwrap(), data);
  }

  if (schema instanceof z.ZodObject) {
    if (data === null || typeof data !== 'object' || Array.isArray(data)) {
      return data;
    }

    const { shape } = schema;
    const record = data as Record<string, unknown>;

    return Object.keys(record).reduce<Record<string, unknown>>((acc, key) => {
      acc[key] = key in shape ? normalizeOptionalNulls(shape[key], record[key]) : record[key];

      return acc;
    }, {});
  }

  return data;
}

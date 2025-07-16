/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { z } from 'zod';

import { objectFromEntries } from './helpers';

const featureNames = ['Variables', 'Providers'] as const;
const featureFlagsDefaults = objectFromEntries(featureNames.map((key) => [key, false]));

const featureFlagsSchema = z
  .object(objectFromEntries(featureNames.map((key) => [key, z.boolean().optional().default(false)])))
  .strict();

export type FeatureFlags = z.infer<typeof featureFlagsSchema>;
export type FeatureName = (typeof featureNames)[number];

export function parseFeatureFlags(data: unknown) {
  const result = featureFlagsSchema.safeParse(data);

  if (!result.success) {
    console.error(result.error);
    return featureFlagsDefaults;
  }

  return result.data;
}

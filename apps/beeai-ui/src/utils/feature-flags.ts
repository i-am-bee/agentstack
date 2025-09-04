/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { z } from 'zod';

import { objectFromEntries } from './helpers';

const featureNames = ['Variables', 'Providers', 'ModelProviders'] as const;
const featureFlagsDefaults = objectFromEntries(
  featureNames.map((key) => {
    if (key === 'ModelProviders') {
      return [key, true] as const;
    }

    return [key, false] as const;
  }),
);

const featureFlagsSchema = z
  .object(objectFromEntries(featureNames.map((key) => [key, z.boolean().optional().default(false)])))
  .strict();

export type FeatureFlags = z.infer<typeof featureFlagsSchema>;
export type FeatureName = (typeof featureNames)[number];

export function parseFeatureFlags(data?: string) {
  if (data) {
    try {
      const featureflags = JSON.parse(data);
      const result = featureFlagsSchema.parse(featureflags);

      return result;
    } catch (error) {
      console.error(error);
    }
  }
  return featureFlagsDefaults;
}

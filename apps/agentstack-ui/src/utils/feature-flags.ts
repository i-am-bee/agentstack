/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { z } from 'zod';

const booleanProp = (defaultValue: boolean | undefined = false) => z.boolean().optional().default(defaultValue);

const featureFlagsSchema = z.strictObject({
  LocalSetup: booleanProp(),
  MCP: booleanProp(),
  ProviderBuilds: booleanProp(),
  Providers: booleanProp(),
  Variables: booleanProp(),
  OAuthConnectors: booleanProp(),
});

export type FeatureFlags = z.infer<typeof featureFlagsSchema>;
export type FeatureName = keyof FeatureFlags;

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

  return featureFlagsSchema.parse({});
}

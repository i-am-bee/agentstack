/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import type { ZodBoolean, ZodDefault } from 'zod';
import z from 'zod';

const Features = ['UserNavigation'];

type FeatureName = (typeof Features)[number];

const featureFlagsSchema = z
  .object(
    Features.reduce(
      (acc, key) => {
        acc[key] = z.boolean().default(false);
        return acc;
      },
      {} as { [K in FeatureName]: ZodDefault<ZodBoolean> },
    ),
  )
  .strict();

function parseFeatureFlags(featureFlagEnv?: string) {
  try {
    const data = JSON.parse(featureFlagEnv ?? '');
    const result = featureFlagsSchema.parse(data);

    return result;
  } catch (err) {
    console.error('Unable to parse feature flags!', err instanceof Error && err.toString());
    return Object.fromEntries(Features.map((feature) => [feature, false])) as Record<FeatureName, boolean>;
  }
}

export const FEATURE_FLAGS = parseFeatureFlags(import.meta.env.VITE_FEATURE_FLAGS);

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

import z from 'zod';

const booleanFlag = z.boolean().default(false);

const featureFlagsSchema = z
  .object({
    UserNavigation: booleanFlag,
  })
  .strict();

export type FeatureFlags = z.infer<typeof featureFlagsSchema>;

export function getFeatureFlags(env: Record<string, string>): FeatureFlags {
  const result = featureFlagsSchema.safeParse(
    (() => {
      try {
        return JSON.parse(env.FEATURE_FLAGS ?? '{}');
      } catch (error) {
        console.error('\n❌  Failed to parse JSON for FEATURE_FLAGS\n');
        throw error;
      }
    })(),
  );

  if (!result.success) {
    console.error('\n❌  Invalid FEATURE_FLAGS\n', result.error.format(), '\n');
    throw result.error;
  }

  return result.data;
}

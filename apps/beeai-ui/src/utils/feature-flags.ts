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

enum FeatureName {
  Settings = 'Settings',
}

function parseFeatureFlags(featureFlagEnv?: string) {
  let features: Record<FeatureName, boolean>;
  try {
    const allFeatures = JSON.parse(featureFlagEnv ?? '');
    features = Object.fromEntries(
      Object.keys(FeatureName).map((feature) => [feature, feature in allFeatures ? !!allFeatures[feature] : false]),
    ) as Record<FeatureName, boolean>;
  } catch (err) {
    console.warn('Unable to parse feature flags!', err);
    features = Object.fromEntries(Object.keys(FeatureName).map((feature) => [feature, false])) as Record<
      FeatureName,
      boolean
    >;
  }
  return features;
}

export const FEATURE_FLAGS = parseFeatureFlags(import.meta.env.VITE_FEATURE_FLAGS);

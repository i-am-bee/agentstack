/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { parseFeatureFlags } from '#utils/feature-flags.ts';

import type { RuntimeConfig } from './types';

export const runtimeConfig: RuntimeConfig = {
  featureFlags: parseFeatureFlags(process.env.FEATURE_FLAGS),
  isAuthEnabled: process.env.OIDC_ENABLED === 'true',
  appName: process.env.APP_NAME || 'Agent Stack',
};

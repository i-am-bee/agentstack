/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { OIDC_ENABLED } from '#utils/constants.ts';
import { parseFeatureFlags } from '#utils/feature-flags.ts';

import type { RuntimeConfig } from './types';

export function getRuntimeConfig(): RuntimeConfig {
  return {
    featureFlags: parseFeatureFlags(process.env.FEATURE_FLAGS),
    isAuthEnabled: OIDC_ENABLED,
    appName: process.env.APP_NAME ?? 'BeeAI',
    companyName: process.env.COMPANY_NAME,
  };
}

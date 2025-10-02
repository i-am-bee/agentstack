/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { APP_NAME, COMPANY_NAME, OIDC_ENABLED } from '#utils/constants.ts';
import { parseFeatureFlags } from '#utils/feature-flags.ts';

import type { RuntimeConfig } from './types';

export function getRuntimeConfig(): RuntimeConfig {
  return {
    featureFlags: parseFeatureFlags(process.env.FEATURE_FLAGS),
    isAuthEnabled: OIDC_ENABLED,
    appName: APP_NAME,
    companyName: COMPANY_NAME,
  };
}

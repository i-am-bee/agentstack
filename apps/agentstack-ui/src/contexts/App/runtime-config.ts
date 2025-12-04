/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { contextTokenPermissionsDefaults } from '#modules/platform-context/constants.ts';
import { contextTokenPermissionsSchema } from '#modules/platform-context/types.ts';
import { featureFlagsDefaults, featureFlagsSchema } from '#utils/feature-flags.ts';
import { loadEnvConfig } from '#utils/helpers.ts';

import type { RuntimeConfig } from './types';

export const runtimeConfig: RuntimeConfig = {
  featureFlags: loadEnvConfig({
    schema: featureFlagsSchema,
    input: process.env.FEATURE_FLAGS,
    defaults: featureFlagsDefaults,
  }),
  contextTokenPermissions: loadEnvConfig({
    schema: contextTokenPermissionsSchema,
    input: process.env.CONTEXT_TOKEN_PERMISSIONS,
    defaults: contextTokenPermissionsDefaults,
  }),
  isAuthEnabled: process.env.OIDC_ENABLED === 'true',
  appName: process.env.APP_NAME || 'Agent Stack',
};

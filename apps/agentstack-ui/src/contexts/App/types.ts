/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ContextTokenPermissions } from '#modules/platform-context/types.ts';
import type { FeatureFlags } from '#utils/feature-flags.ts';

export enum SidePanelVariant {
  AgentDetail = 'AgentDetail',
  Sources = 'Sources',
}

export interface RuntimeConfig {
  featureFlags: FeatureFlags;
  contextTokenPermissions: ContextTokenPermissions;
  isAuthEnabled: boolean;
  appName: string;
}

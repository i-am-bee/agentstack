/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ProviderBuild } from '#modules/provider-builds/api/types.ts';
import type { RegisterProviderRequest } from '#modules/providers/api/types.ts';
import type { ProviderSource } from '#modules/providers/types.ts';

export type ImportAgentFormValues = RegisterProviderRequest & {
  source: ProviderSource;
  action?: ProviderBuild['on_complete']['type'];
  providerId?: string;
};

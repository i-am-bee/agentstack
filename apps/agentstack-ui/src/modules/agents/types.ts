/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { CreateProviderRequest } from 'agentstack-sdk';

import type { ProviderSource } from '#modules/providers/types.ts';

export type ImportAgentFormValues = CreateProviderRequest & {
  source: ProviderSource;
  providerId?: string;
};

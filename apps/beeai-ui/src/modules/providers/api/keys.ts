/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ListProvidersParams, ReadProviderPath } from './types';

export const providerKeys = {
  all: () => ['providers'] as const,
  lists: () => [...providerKeys.all(), 'list'] as const,
  list: ({ query = {} }: ListProvidersParams = {}) => [...providerKeys.lists(), query] as const,
  details: () => [...providerKeys.all(), 'detail'] as const,
  detail: ({ id }: ReadProviderPath) => [...providerKeys.details(), id] as const,
};

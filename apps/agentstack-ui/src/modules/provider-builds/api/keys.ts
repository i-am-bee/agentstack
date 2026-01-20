/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ReadProviderBuildLogsRequest, ReadProviderBuildRequest } from 'agentstack-sdk';

export const providerBuildKeys = {
  all: () => ['provider-builds'] as const,
  lists: () => [...providerBuildKeys.all(), 'list'] as const,
  list: () => [...providerBuildKeys.lists()] as const,
  details: () => [...providerBuildKeys.all(), 'detail'] as const,
  detail: ({ id }: ReadProviderBuildRequest) => [...providerBuildKeys.details(), id] as const,
  logs: () => [...providerBuildKeys.all(), 'logs'] as const,
  log: ({ id }: ReadProviderBuildLogsRequest) => [...providerBuildKeys.logs(), id] as const,
};

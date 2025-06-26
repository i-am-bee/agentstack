/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

export const providerKeys = {
  all: () => ['providers'] as const,
  lists: () => [...providerKeys.all(), 'list'] as const,
  list: () => [...providerKeys.lists()] as const,
  details: () => [...providerKeys.all(), 'detail'] as const,
  detail: (id: string) => [...providerKeys.details(), id] as const,
};

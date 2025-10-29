/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

export const providerVariableKeys = {
  all: () => ['providers', 'variables'] as const,
  lists: () => [...providerVariableKeys.all(), 'list'] as const,
  list: (providerId: string) => [...providerVariableKeys.lists(), providerId],
};

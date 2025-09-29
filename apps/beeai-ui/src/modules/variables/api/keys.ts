/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

export const variableKeys = {
  all: () => ['variables'] as const,
  lists: () => [...variableKeys.all(), 'list'] as const,
  list: (providerId: string) => [...variableKeys.lists(), providerId],
};

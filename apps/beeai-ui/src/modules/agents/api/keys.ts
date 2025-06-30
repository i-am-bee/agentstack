/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

export const agentKeys = {
  all: () => ['agents'] as const,
  lists: () => [...agentKeys.all(), 'list'] as const,
  list: ({ providerId }: { providerId?: string } = {}) => [...agentKeys.lists(), { providerId }] as const,
};

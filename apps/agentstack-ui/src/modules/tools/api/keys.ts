/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

export const toolKeys = {
  all: () => ['tools'] as const,
  lists: () => [...toolKeys.all(), 'list'] as const,
  list: () => [...toolKeys.lists()] as const,
};

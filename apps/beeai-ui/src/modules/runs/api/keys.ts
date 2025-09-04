/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

export const runKeys = {
  all: () => ['run'] as const,
  clients: () => [...runKeys.all(), 'client'] as const,
  client: (id: string) => [...runKeys.clients(), id] as const,
};

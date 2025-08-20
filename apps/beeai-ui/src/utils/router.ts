/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

export const routes = {
  home: () => '/' as const,
  notFound: () => '/not-found' as const,
  agentRun: ({ p }: { p: string }) => `/run?p=${p}`,
  playground: () => '/playground' as const,
  playgroundSequential: () => '/playground/sequential' as const,
  settings: () => '/settings' as const,
};

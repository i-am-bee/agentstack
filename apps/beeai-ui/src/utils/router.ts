/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

export const routes = {
  home: () => '/' as const,
  login: () => '/signin' as const,
  notFound: () => '/not-found' as const,
  agentRun: ({ name }: { name: string }) => `/run?agent=${name}`,
  playground: () => '/playground' as const,
  playgroundSequential: () => '/playground/sequential' as const,
  settings: () => '/settings' as const,
};

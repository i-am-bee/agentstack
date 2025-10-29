/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

export const routeDefinitions = {
  home: '/' as const,
  notFound: '/not-found' as const,
  agents: `/agents` as const,
  agentDetail: `/agents/[name]` as const,
  blog: '/blog' as const,
};

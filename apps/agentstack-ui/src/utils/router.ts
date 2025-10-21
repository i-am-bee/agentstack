/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { AuthError } from 'next-auth';

export const routes = {
  home: () => '/' as const,
  error: ({ error }: { error: AuthError }) => `/error?error=${error.type}`,
  signIn: ({ callbackUrl }: { callbackUrl?: string } = {}) =>
    `/signin${callbackUrl ? `?callbackUrl=${encodeURIComponent(callbackUrl)}` : ''}`,
  notFound: () => '/not-found' as const,
  agentRun: ({ providerId, contextId }: AgentRunParams) =>
    `/run/${encodeURIComponent(providerId)}${contextId ? `/c/${encodeURIComponent(contextId)}` : ''}`,
  playground: () => '/playground' as const,
  playgroundSequential: () => '/playground/sequential' as const,
  settings: () => '/settings' as const,
};

interface AgentRunParams {
  providerId: string;
  contextId?: string;
}

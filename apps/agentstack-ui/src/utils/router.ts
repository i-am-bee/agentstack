/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

export const routes = {
  home: () => '/' as const,
  signIn: ({ callbackUrl }: { callbackUrl?: string } = {}) =>
    `/signin${callbackUrl ? `?callbackUrl=${encodeURIComponent(callbackUrl)}` : ''}`,
  notFound: () => '/not-found' as const,
  agentRun: ({ providerId, contextId }: AgentRunParams) =>
    `/run/${encodeURIComponent(providerId)}${contextId ? `/c/${encodeURIComponent(contextId)}` : ''}`,
  settings: () => '/settings' as const,
};

interface AgentRunParams {
  providerId: string;
  contextId?: string;
}

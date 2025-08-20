/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useListAgents } from '#modules/agents/api/queries/useListAgents.ts';

import { useProviderIdFromUrl } from './useProviderIdFromUrl';

export function useCurrentAgentName() {
  const providerId = useProviderIdFromUrl();

  const { data: agents } = useListAgents({ onlyUiSupported: true, sort: true });

  if (!providerId || !agents) {
    return null;
  }

  return agents.find(({ provider: { id } }) => providerId === id)?.name ?? null;
}

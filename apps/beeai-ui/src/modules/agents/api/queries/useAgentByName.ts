/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQuery } from '@tanstack/react-query';

import { buildAgent } from '#modules/agents/utils.ts';
import { listProviders } from '#modules/providers/api/index.ts';
import { providerKeys } from '#modules/providers/api/keys.ts';

export function useAgentByName({ name }: { name: string }) {
  return useQuery({
    queryKey: providerKeys.list(),
    queryFn: listProviders,
    select: (response) => {
      const agentProvider = response?.items.find(({ agent_card }) => agent_card.name === name);
      return agentProvider ? buildAgent(agentProvider) : undefined;
    },
  });
}

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQuery } from '@tanstack/react-query';

import { buildAgent } from '#modules/agents/utils.ts';
import { listProviders } from '#modules/providers/api/index.ts';
import { providerKeys } from '#modules/providers/api/keys.ts';

interface Props {
  providerId: string | null | undefined;
}

export function useAgent({ providerId }: Props) {
  return useQuery({
    queryKey: providerKeys.list(),
    queryFn: listProviders,
    select: (response) => {
      const agentProvider = response?.items.find(({ id }) => id === providerId);
      return agentProvider ? buildAgent(agentProvider) : undefined;
    },
    enabled: Boolean(providerId),
  });
}

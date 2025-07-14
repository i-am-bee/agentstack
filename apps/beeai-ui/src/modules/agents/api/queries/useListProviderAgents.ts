/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQuery } from '@tanstack/react-query';

import { buildAgent } from '#modules/agents/utils.ts';
import { readProvider } from '#modules/providers/api/index.ts';

import { agentKeys } from '../keys';

interface Props {
  providerId?: string;
  enabled?: boolean;
}

export function useListProviderAgents({ providerId, enabled = true }: Props) {
  const query = useQuery({
    queryKey: agentKeys.list({ providerId }),
    queryFn: () => readProvider(providerId!),
    enabled: Boolean(enabled && providerId),
    // Retaining the Agent[] type for now to avoid unnecessary refactoring,
    // in case the structure changes back in the future.
    select: (provider) => (provider ? [buildAgent(provider)] : []),
  });

  return query;
}

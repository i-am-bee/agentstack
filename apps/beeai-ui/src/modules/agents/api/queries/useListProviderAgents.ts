/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQuery } from '@tanstack/react-query';

import { listAgents } from '..';
import { agentKeys } from '../keys';
import type { Agent } from '../types';

interface Props {
  providerId?: string;
  enabled?: boolean;
}

export function useListProviderAgents({ providerId, enabled = true }: Props) {
  const query = useQuery({
    queryKey: agentKeys.list({ providerId }),
    queryFn: listAgents,
    enabled: Boolean(enabled && providerId),
    select: (data) => data?.agents.filter(({ metadata }) => metadata.provider_id === providerId) as Agent[],
  });

  return query;
}

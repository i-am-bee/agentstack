/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMemo } from 'react';

import { useListAgents } from '#modules/agents/api/queries/useListAgents.ts';
import { isAgentUiSupported, sortAgentsByName } from '#modules/agents/utils.ts';

export function useSequentialCompatibleAgents() {
  const { data, isPending } = useListAgents();
  const agents = useMemo(() => data?.filter(isAgentUiSupported).sort(sortAgentsByName), [data]);

  return { agents, isPending };
}

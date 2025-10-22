/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useListAgents } from '#modules/agents/api/queries/useListAgents.ts';
import { ListAgentsOrderBy } from '#modules/agents/api/types.ts';

export function useSequentialCompatibleAgents() {
  const { data: agents, isPending } = useListAgents({ onlyUiSupported: true, orderBy: ListAgentsOrderBy.Name });

  return { agents, isPending };
}

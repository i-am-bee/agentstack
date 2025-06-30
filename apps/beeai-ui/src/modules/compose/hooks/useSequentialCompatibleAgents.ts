/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMemo } from 'react';

import { useListAgents } from '#modules/agents/api/queries/useListAgents.ts';
import { UiType } from '#modules/agents/api/types.ts';
import { sortAgentsByName } from '#modules/agents/utils.ts';

const SupportedUis: UiType[] = [UiType.HandsOff];

export function useSequentialCompatibleAgents() {
  const { data, isPending } = useListAgents();
  const agents = useMemo(
    () =>
      data
        ?.filter((agent) => SupportedUis.includes(agent.metadata.annotations?.beeai_ui?.ui_type as UiType))
        .sort(sortAgentsByName),
    [data],
  );

  return { agents, isPending };
}

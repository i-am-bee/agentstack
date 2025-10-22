/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMemo } from 'react';

import { useListAgents } from '#modules/agents/api/queries/useListAgents.ts';
import { ListAgentsOrderBy } from '#modules/agents/api/types.ts';
import type { ListProvidersResponse } from '#modules/providers/api/types.ts';
import { isRecentlyUsedAgent } from '#modules/providers/utils.ts';

import { USER_NOT_OWNED_AGENTS_LIST_PARAMS } from '../constants';

interface Props {
  initialData?: ListProvidersResponse;
}

export function useRecentlyUsedAgents({ initialData }: Props = {}) {
  const { data, ...query } = useListAgents({
    ...USER_NOT_OWNED_AGENTS_LIST_PARAMS,
    onlyUiSupported: true,
    orderBy: ListAgentsOrderBy.LastActiveAt,
    initialData,
  });

  const agents = useMemo(() => data?.filter(isRecentlyUsedAgent), [data]);

  return {
    ...query,
    data: agents,
  };
}

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useListAgents } from '#modules/agents/api/queries/useListAgents.ts';
import { ListAgentsOrderBy } from '#modules/agents/api/types.ts';
import type { ListProvidersResponse } from '#modules/providers/api/types.ts';

import { USER_OWNED_AGENTS_LIST_PARAMS } from '../constants';

interface Props {
  initialData?: ListProvidersResponse;
}

export function useRecentlyAddedAgents({ initialData }: Props = {}) {
  const query = useListAgents({
    ...USER_OWNED_AGENTS_LIST_PARAMS,
    onlyUiSupported: true,
    orderBy: ListAgentsOrderBy.CreatedAt,
    initialData,
  });

  return query;
}

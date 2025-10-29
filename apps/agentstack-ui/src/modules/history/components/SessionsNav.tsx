/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMemo } from 'react';

import { NavGroup } from '#components/Sidebar/NavGroup.tsx';
import { useFetchNextPage } from '#hooks/useFetchNextPage.ts';
import { useParamsFromUrl } from '#hooks/useParamsFromUrl.ts';
import { useListAgents } from '#modules/agents/api/queries/useListAgents.ts';
import { LIST_CONTEXTS_DEFAULT_QUERY } from '#modules/platform-context/api/constants.ts';
import { useListContexts } from '#modules/platform-context/api/queries/useListContexts.ts';
import { isNotNull } from '#utils/helpers.ts';
import { routes } from '#utils/router.ts';

import { SessionsList } from './SessionsList';

export function SessionsNav() {
  const { data: agents } = useListAgents();
  const { providerId: providerIdUrlParam, contextId: contextIdUrlParam } = useParamsFromUrl();
  const { data, isLoading, isFetching, hasNextPage, fetchNextPage } = useListContexts({
    query: LIST_CONTEXTS_DEFAULT_QUERY,
  });
  const { ref: fetchNextPageRef } = useFetchNextPage({
    isFetching,
    hasNextPage,
    fetchNextPage,
  });

  const items = useMemo(
    () =>
      data
        ?.map(({ id: contextId, created_at, metadata }) => {
          const providerId = metadata?.provider_id;
          const agent = agents?.find((agent) => agent.provider.id === providerId);
          const heading = (metadata?.title || created_at) ?? '';
          const agentName = agent?.name || metadata?.agentName;
          const isActive = providerIdUrlParam === providerId && contextIdUrlParam === contextId;

          if (!providerId || !contextId) {
            return null;
          }

          return {
            contextId,
            providerId,
            href: routes.agentRun({ providerId, contextId }),
            heading,
            agentName,
            isActive,
          };
        })
        .filter(isNotNull),
    [data, agents, providerIdUrlParam, contextIdUrlParam],
  );

  return (
    <NavGroup heading="Sessions">
      <SessionsList items={items} isLoading={isLoading} />

      {hasNextPage && <div ref={fetchNextPageRef} />}
    </NavGroup>
  );
}

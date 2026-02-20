/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMemo } from 'react';

import { NavGroup } from '#components/Navbar/NavGroup.tsx';
import { useFetchNextPage } from '#hooks/useFetchNextPage.ts';
import { useParamsFromUrl } from '#hooks/useParamsFromUrl.ts';
import { useListAgents } from '#modules/agents/api/queries/useListAgents.ts';
import { LIST_CONTEXTS_DEFAULT_QUERY } from '#modules/platform-context/api/constants.ts';
import { useListContexts } from '#modules/platform-context/api/queries/useListContexts.ts';
import { isNotNull } from '#utils/helpers.ts';

import { SessionsList } from './SessionsList';

interface Props {
  className?: string;
}

export function SessionsNav({ className }: Props) {
  const { contextId: contextIdUrl, providerId: providerIdUrl } = useParamsFromUrl();

  const { data: agents, isLoading: isAgentsLoading } = useListAgents({ includeOffline: true });
  const { data, isLoading, isFetching, hasNextPage, fetchNextPage } = useListContexts({
    query: { ...LIST_CONTEXTS_DEFAULT_QUERY, provider_id: providerIdUrl },
  });
  const { ref: fetchNextPageRef } = useFetchNextPage({ isFetching, hasNextPage, fetchNextPage });

  const items = useMemo(() => {
    if (!agents) {
      return undefined;
    }

    const agentsMap = new Map(agents.map((agent) => [agent.provider.id, agent]));

    return data
      ?.map(({ id: contextId, created_at, metadata, provider_id }) => {
        const providerId = provider_id ?? metadata?.provider_id;
        const agent = providerId ? agentsMap.get(providerId) : undefined;

        if (!providerId || !contextId || !agent) {
          return null;
        }

        const heading = (metadata?.title || created_at) ?? contextId;
        const isActive = contextIdUrl === contextId;

        return {
          contextId,
          providerId,
          heading,
          isActive,
        };
      })
      .filter(isNotNull);
  }, [data, agents, contextIdUrl]);

  return (
    <NavGroup heading="Sessions" className={className}>
      <SessionsList items={items} isLoading={isLoading || isAgentsLoading} />

      {hasNextPage && <div ref={fetchNextPageRef} />}
    </NavGroup>
  );
}

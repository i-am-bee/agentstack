/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMemo } from 'react';

import { NavGroup } from '#components/Sidebar/NavGroup.tsx';
import { useFetchNextPage } from '#hooks/useFetchNextPage.ts';
import { useParamsFromUrl } from '#hooks/useParamsFromUrl.ts';
import { LIST_CONTEXTS_DEFAULT_QUERY } from '#modules/platform-context/api/constants.ts';
import { useListContexts } from '#modules/platform-context/api/queries/useListContexts.ts';
import { isNotNull } from '#utils/helpers.ts';

import { SessionsList } from './SessionsList';

interface Props {
  providerId: string;
  className?: string;
}

export function SessionsNav({ providerId, className }: Props) {
  const { contextId: contextIdUrl } = useParamsFromUrl();
  const { data, isLoading, isFetching, hasNextPage, fetchNextPage } = useListContexts({
    query: {
      ...LIST_CONTEXTS_DEFAULT_QUERY,
      provider_id: providerId,
    },
  });
  const { ref: fetchNextPageRef } = useFetchNextPage({ isFetching, hasNextPage, fetchNextPage });

  const items = useMemo(
    () =>
      data
        ?.map(({ id: contextId, created_at, metadata }) => {
          if (!contextId) {
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
        .filter(isNotNull),
    [data, contextIdUrl, providerId],
  );

  return (
    <NavGroup heading="Sessions" className={className}>
      <SessionsList items={items} isLoading={isLoading} />

      {hasNextPage && <div ref={fetchNextPageRef} />}
    </NavGroup>
  );
}

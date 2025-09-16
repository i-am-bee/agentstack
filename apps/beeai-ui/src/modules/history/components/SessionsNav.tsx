/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMemo } from 'react';

import { NavGroup } from '#components/SidePanel/NavGroup.tsx';
import { useFetchNextPage } from '#hooks/useFetchNextPage.ts';
import { useListContexts } from '#modules/platform-context/api/queries/useListContexts.ts';
import { routes } from '#utils/router.ts';

import type { SessionItem } from './SessionItem';
import { SessionsList } from './SessionsList';

export function SessionsNav() {
  const { data, isFetching, hasNextPage, fetchNextPage } = useListContexts({ query: { limit: 10 } });
  const { ref: fetchNextPageRef } = useFetchNextPage({ isFetching, hasNextPage, fetchNextPage });

  const items = useMemo(
    () =>
      data?.map(
        ({ id, created_at }) =>
          ({
            href: routes.agentRun({ providerId: '#todo', contextId: id }),
            heading: created_at,
            agentName: '#todo',
          }) as SessionItem,
      ),
    [data],
  );

  return (
    <NavGroup heading="Sessions" toggleable>
      <SessionsList items={items} />

      {hasNextPage && <div ref={fetchNextPageRef} />}
    </NavGroup>
  );
}

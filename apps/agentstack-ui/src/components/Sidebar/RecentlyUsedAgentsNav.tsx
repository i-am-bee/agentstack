/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMemo } from 'react';

import { useListAgents } from '#modules/agents/api/queries/useListAgents.ts';
import { ListAgentsOrderBy } from '#modules/agents/api/types.ts';
import { routes } from '#utils/router.ts';

import { NavGroup } from './NavGroup';
import { NavList } from './NavList';

interface Props {
  className?: string;
}

export function RecentlyUsedAgentsNav({ className }: Props) {
  const { data: agents, isLoading } = useListAgents({
    onlyUiSupported: true,
    orderBy: ListAgentsOrderBy.LastActiveAt,
  });

  const items = useMemo(
    () =>
      agents
        ?.filter(({ provider: { created_at: createdAt, last_active_at: lastActiveAt } }) => {
          if (!createdAt || !lastActiveAt) {
            return false;
          }

          const diff = new Date(lastActiveAt).getTime() - new Date(createdAt).getTime();

          return diff > RECENT_THRESHOLD_MS;
        })
        .map(({ name, provider: { id } }) => ({
          label: name,
          href: routes.agentRun({ providerId: id }),
        })),
    [agents],
  );

  return (
    <NavGroup heading="Recently used agents" className={className}>
      <NavList items={items} isLoading={isLoading} skeletonCount={5} noItemsMessage="No history" />
    </NavGroup>
  );
}

const RECENT_THRESHOLD_MS = 60_000;

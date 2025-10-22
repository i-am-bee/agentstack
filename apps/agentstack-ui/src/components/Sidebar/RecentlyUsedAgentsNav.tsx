/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMemo } from 'react';

import { useRecentlyUsedAgents } from '#modules/home/hooks/useRecentlyUsedAgents.ts';
import { routes } from '#utils/router.ts';

import { NavGroup } from './NavGroup';
import { NavList } from './NavList';

interface Props {
  className?: string;
}

export function RecentlyUsedAgentsNav({ className }: Props) {
  const { data: agents, isLoading } = useRecentlyUsedAgents();

  const items = useMemo(
    () =>
      agents?.map(({ name, provider: { id } }) => ({
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

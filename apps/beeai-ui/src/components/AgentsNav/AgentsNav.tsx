/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { usePathname, useSearchParams } from 'next/navigation';

import type { NavItem } from '#components/SidePanel/Nav.tsx';
import { Nav } from '#components/SidePanel/Nav.tsx';
import { useRouteTransition } from '#contexts/TransitionContext/index.ts';
import { useListAgents } from '#modules/agents/api/queries/useListAgents.ts';
import { routes } from '#utils/router.ts';

export function AgentsNav() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { transitionTo } = useRouteTransition();

  const { data: agents } = useListAgents({ onlyUiSupported: true, sort: true });

  const items: NavItem[] | undefined = agents?.map(({ name }) => {
    const route = routes.agentRun({ name });
    const fullPath = `${pathname}?${searchParams.toString()}`;

    return {
      key: name,
      label: name,
      isActive: fullPath === route,
      onClick: () => transitionTo(route),
    };
  });

  return <Nav title="Agents" items={items} skeletonCount={10} />;
}

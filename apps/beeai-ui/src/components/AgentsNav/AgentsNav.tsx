/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { NavItem } from '#components/SidePanel/Nav.tsx';
import { Nav } from '#components/SidePanel/Nav.tsx';
import { useRouteTransition } from '#contexts/TransitionContext/index.ts';
import { useProviderIdFromUrl } from '#hooks/useProviderIdFromUrl.ts';
import { useListAgents } from '#modules/agents/api/queries/useListAgents.ts';
import { routes } from '#utils/router.ts';

export function AgentsNav() {
  const providerId = useProviderIdFromUrl();
  const { transitionTo } = useRouteTransition();

  const { data: agents } = useListAgents({ onlyUiSupported: true, sort: true });

  const items: NavItem[] | undefined = agents?.map(({ name, provider: { id } }) => {
    const route = routes.agentRun({ p: id });

    return {
      key: id,
      label: name,
      isActive: providerId === id,
      onClick: () => transitionTo(route),
    };
  });

  return <Nav title="Agents" items={items} skeletonCount={10} />;
}

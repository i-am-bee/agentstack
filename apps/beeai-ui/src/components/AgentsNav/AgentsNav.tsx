/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { NavItem } from '#components/SidePanel/Nav.tsx';
import { Nav } from '#components/SidePanel/Nav.tsx';
import { useRouteTransition } from '#contexts/TransitionContext/index.ts';
import { useAgentNameFromPath } from '#hooks/useAgentNameFromPath.ts';
import { useListAgents } from '#modules/agents/api/queries/useListAgents.ts';
import { routes } from '#utils/router.ts';

export function AgentsNav() {
  const agentName = useAgentNameFromPath();
  const { transitionTo } = useRouteTransition();

  const { data: agents } = useListAgents({ onlyUiSupported: true, sort: true });

  const items: NavItem[] | undefined = agents?.map(({ name }) => {
    const route = routes.agentRun({ name });

    return {
      key: name,
      label: name,
      isActive: agentName === name,
      onClick: () => transitionTo(route),
    };
  });

  return <Nav title="Agents" items={items} skeletonCount={10} />;
}

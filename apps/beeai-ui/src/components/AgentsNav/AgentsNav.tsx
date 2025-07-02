/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { usePathname } from 'next/navigation';

import type { NavItem } from '#components/SidePanel/Nav.tsx';
import { Nav } from '#components/SidePanel/Nav.tsx';
import { useRouteTransition } from '#contexts/TransitionContext/index.ts';
import { useListAgents } from '#modules/agents/api/queries/useListAgents.ts';
import { getAgentUiMetadata } from '#modules/agents/utils.ts';
import { routes } from '#utils/router.ts';

export function AgentsNav() {
  const pathname = usePathname();
  const { transitionTo } = useRouteTransition();

  const { data: agents } = useListAgents({ onlyUiSupported: true, sort: true });

  const items: NavItem[] | undefined = agents?.map((agent) => {
    const route = routes.agentRun({ name: agent.name });
    return {
      key: agent.name,
      label: getAgentUiMetadata(agent).display_name,
      isActive: pathname === route,
      onClick: () => transitionTo(route),
    };
  });

  return <Nav title="Agents" items={items} skeletonCount={10} />;
}

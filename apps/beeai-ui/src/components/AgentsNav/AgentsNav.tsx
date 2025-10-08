/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { NavGroup } from '#components/SidePanel/NavGroup.tsx';
import type { NavItem } from '#components/SidePanel/NavItem.tsx';
import { NavList } from '#components/SidePanel/NavList.tsx';
import { useParamsFromUrl } from '#hooks/useParamsFromUrl.ts';
import { useListAgents } from '#modules/agents/api/queries/useListAgents.ts';
import { routes } from '#utils/router.ts';

interface Props {
  className?: string;
  bodyClassName?: string;
}

export function AgentsNav({ className, bodyClassName }: Props) {
  const { providerId } = useParamsFromUrl();

  const { data: agents } = useListAgents({ onlyUiSupported: true, sort: true });

  const items: NavItem[] | undefined = agents?.map(({ name, provider: { id } }) => ({
    key: id,
    href: routes.agentRun({ providerId: id }),
    label: name,
    isActive: providerId === id,
  }));

  return (
    <NavGroup heading="Agents" className={className} bodyClassName={bodyClassName}>
      <NavList items={items} skeletonCount={5} />
    </NavGroup>
  );
}

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMemo } from 'react';

import { useModal } from '#contexts/Modal/index.tsx';
import { useParamsFromUrl } from '#hooks/useParamsFromUrl.ts';
import { useListAgents } from '#modules/agents/api/queries/useListAgents.ts';
import { ListAgentsOrderBy } from '#modules/agents/api/types.ts';
import { ImportAgentsModal } from '#modules/agents/components/import/ImportAgentsModal.tsx';
import { useCanManageProviders } from '#modules/providers/hooks/useCanManageProviders.ts';
import { routes } from '#utils/router.ts';

import { NavGroup } from './NavGroup';
import { NavList } from './NavList';

interface Props {
  className?: string;
}

export function AgentsNav({ className }: Props) {
  const { openModal } = useModal();

  const { providerId: providerIdUrl } = useParamsFromUrl();
  const canManageProviders = useCanManageProviders();

  const { data: agents, isLoading } = useListAgents({ orderBy: ListAgentsOrderBy.Name });

  const action = useMemo(
    () =>
      canManageProviders
        ? {
            label: 'Add new agent',
            onClick: () => openModal((props) => <ImportAgentsModal {...props} />),
          }
        : undefined,
    [canManageProviders, openModal],
  );

  const items = useMemo(
    () =>
      agents?.map(({ name, provider: { id } }) => ({
        label: name,
        href: routes.agentRun({ providerId: id }),
        isActive: providerIdUrl === id,
      })),
    [agents, providerIdUrl],
  );

  return (
    <NavGroup heading="Agents" className={className} action={action}>
      <NavList items={items} isLoading={isLoading} skeletonCount={5} noItemsMessage="No agent added" />
    </NavGroup>
  );
}

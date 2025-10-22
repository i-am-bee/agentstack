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
import { routes } from '#utils/router.ts';

import { NavGroup } from './NavGroup';
import { NavList } from './NavList';

interface Props {
  className?: string;
}

export function AgentsNav({ className }: Props) {
  const { providerId } = useParamsFromUrl();
  const { openModal } = useModal();

  const { data: agents, isLoading } = useListAgents({
    query: { user_owned: true },
    onlyUiSupported: true,
    orderBy: ListAgentsOrderBy.CreatedAt,
  });

  const action = useMemo(
    () => ({
      label: 'Add new agent',
      onClick: () => openModal((props) => <ImportAgentsModal {...props} />),
    }),
    [openModal],
  );

  const items = useMemo(
    () =>
      agents?.map(({ name, provider: { id } }) => ({
        label: name,
        href: routes.agentRun({ providerId: id }),
        isActive: providerId === id,
      })),
    [agents, providerId],
  );

  return (
    <NavGroup heading="Agents added by me" className={className} action={action}>
      <NavList items={items} isLoading={isLoading} skeletonCount={5} noItemsMessage="No agent added" />
    </NavGroup>
  );
}

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useMemo } from 'react';

import { useApp } from '#contexts/App/index.ts';
import { useModal } from '#contexts/Modal/index.tsx';
import { useParamsFromUrl } from '#hooks/useParamsFromUrl.ts';
import { useListAgents } from '#modules/agents/api/queries/useListAgents.ts';
import { ListAgentsOrderBy } from '#modules/agents/api/types.ts';
import { ImportAgentsModal } from '#modules/agents/components/import/ImportAgentsModal.tsx';
import { useUser } from '#modules/users/api/queries/useUser.ts';
import { isUserAdminOrDev } from '#modules/users/utils.ts';
import { routes } from '#utils/router.ts';

import { NavGroup } from './NavGroup';
import { NavList } from './NavList';

interface Props {
  className?: string;
}

export function AgentsNav({ className }: Props) {
  const { openModal } = useModal();
  const {
    config: { featureFlags },
  } = useApp();
  const { providerId: providerIdUrl } = useParamsFromUrl();
  const { data: user } = useUser();
  const { data: agents, isLoading } = useListAgents({ orderBy: ListAgentsOrderBy.Name });

  const isAdminOrDev = isUserAdminOrDev(user);

  const action = useMemo(
    () =>
      featureFlags.Providers && isAdminOrDev
        ? {
            label: 'Add new agent',
            onClick: () => openModal((props) => <ImportAgentsModal {...props} />),
          }
        : undefined,
    [featureFlags.Providers, isAdminOrDev, openModal],
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

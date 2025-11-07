/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Code, Information } from '@carbon/icons-react';
import { useMemo } from 'react';

import { useApp } from '#contexts/App/index.ts';
import { SidePanelVariant } from '#contexts/App/types.ts';
import { useAgent } from '#modules/agents/api/queries/useAgent.ts';
import { isNotNull } from '#utils/helpers.ts';
import { routes } from '#utils/router.ts';

import { NavGroup } from './NavGroup';
import { NavList } from './NavList';
import NewSession from './NewSession.svg';

interface Props {
  providerId: string;
}

export function AgentNav({ providerId }: Props) {
  const { openSidePanel } = useApp();

  const { data: agent, isLoading } = useAgent({ providerId });

  const sourceCodeUrl = agent?.ui.source_code_url;

  const items = useMemo(() => {
    return [
      {
        label: 'New session',
        Icon: NewSession,
        href: routes.agentRun({ providerId }),
      },
      // {
      //   label: 'Secrets',
      //   Icon: Password,
      // },
      {
        label: 'About',
        Icon: Information,
        onClick: () => openSidePanel(SidePanelVariant.AgentDetail),
      },
      sourceCodeUrl
        ? {
            label: 'View source code',
            Icon: Code,
            href: sourceCodeUrl,
            isExternal: true,
          }
        : null,
    ].filter(isNotNull);
  }, [providerId, sourceCodeUrl, openSidePanel]);

  return (
    <NavGroup heading={agent?.name} isLoading={isLoading}>
      <NavList items={items} isLoading={isLoading} skeletonCount={4} />
    </NavGroup>
  );
}

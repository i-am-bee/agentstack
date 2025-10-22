/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Information } from '@carbon/icons-react';
import { useMemo } from 'react';

import { useApp } from '#contexts/App/index.ts';
import { SidePanelVariant } from '#contexts/App/types.ts';
import type { Agent } from '#modules/agents/api/types.ts';
import { routes } from '#utils/router.ts';

import NewSession from '../../modules/runs/components/NewSession.svg';
import { NavGroup } from './NavGroup';
import { NavList } from './NavList';

interface Props {
  agent: Agent;
}

export function AgentNav({ agent }: Props) {
  const { openSidePanel } = useApp();

  const items = useMemo(() => {
    return [
      {
        label: 'New session',
        href: routes.agentRun({ providerId: agent.provider.id }),
        Icon: NewSession,
      },
      // {
      //   label: 'Agent secrets',
      //   Icon: Password,
      // },
      {
        label: 'About agent',
        Icon: Information,
        onClick: () => openSidePanel(SidePanelVariant.AgentDetail),
      },
    ];
  }, [agent.provider.id, openSidePanel]);

  return (
    <NavGroup heading={agent.name}>
      <NavList items={items} />
    </NavGroup>
  );
}

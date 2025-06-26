/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { type Agent, AgentsFiltersProvider } from '@i-am-bee/beeai-ui';

import { AgentsView } from './AgentsView';

interface Props {
  agents: Agent[] | null;
}

export function AgentsFilteredView({ agents }: Props) {
  return (
    <AgentsFiltersProvider>
      <AgentsView agents={agents} />
    </AgentsFiltersProvider>
  );
}

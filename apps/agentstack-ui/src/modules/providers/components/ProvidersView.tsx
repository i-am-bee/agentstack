/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button } from '@carbon/react';
import { useMemo } from 'react';

import { TableViewActions } from '#components/TableView/TableViewActions.tsx';
import { TableViewWithSearch } from '#components/TableView/TableViewWithSearch.tsx';
import { useModal } from '#contexts/Modal/index.tsx';
import { useListAgents } from '#modules/agents/api/queries/useListAgents.ts';
import { ListAgentsOrderBy } from '#modules/agents/api/types.ts';
import { ImportAgentsModal } from '#modules/agents/components/import/ImportAgentsModal.tsx';
import { getAgentsProgrammingLanguages } from '#modules/agents/utils.ts';
import { isNotNull } from '#utils/helpers.ts';

import { useListProviders } from '../api/queries/useListProviders';
import { groupAgentsByProvider } from '../utils';
import { DeleteProviderButton } from './DeleteProviderButton';
import classes from './ProvidersView.module.scss';

export function ProvidersView() {
  const { openModal } = useModal();

  const { data: providers, isPending: isProvidersPending } = useListProviders();
  const { data: agents, isPending: isAgentsPending } = useListAgents({
    includeOffline: true,
    includeUnsupportedUi: true,
    orderBy: ListAgentsOrderBy.CreatedAt,
  });

  const agentsByProvider = useMemo(() => groupAgentsByProvider(agents), [agents]);

  const headers = [
    { key: 'source', header: 'Source', className: classes.source },
    { key: 'runtime', header: 'Runtime' },
    { key: 'agents', header: <>#&nbsp;of&nbsp;agents</>, className: classes.agents },
    { key: 'actions', header: '' },
  ];

  const entries = useMemo(() => {
    if (!providers) {
      return [];
    }

    return providers.items
      .map((provider) => {
        const { id, source } = provider;
        const agents = agentsByProvider[id] ?? [];
        const agentsCount = agents.length;

        if (agentsCount === 0) {
          return null;
        }

        return {
          id,
          source,
          runtime: getAgentsProgrammingLanguages(agents).join(', '),
          agents: agentsCount,
          actions: (
            <TableViewActions>
              <DeleteProviderButton provider={provider} />
            </TableViewActions>
          ),
        };
      })
      .filter(isNotNull);
  }, [providers, agentsByProvider]);

  const isPending = isProvidersPending || isAgentsPending;

  return (
    <TableViewWithSearch
      className={classes.root}
      headers={headers}
      entries={entries}
      searchFields={['id', 'source', 'runtime']}
      isPending={isPending}
      toolbarButton={<Button onClick={() => openModal((props) => <ImportAgentsModal {...props} />)}>Add agent</Button>}
    />
  );
}

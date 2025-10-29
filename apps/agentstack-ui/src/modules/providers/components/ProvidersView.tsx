/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import {
  Button,
  DataTable,
  DataTableSkeleton,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@carbon/react';
import { useMemo } from 'react';

import { TableView } from '#components/TableView/TableView.tsx';
import { TableViewActions } from '#components/TableView/TableViewActions.tsx';
import { TableViewToolbar } from '#components/TableView/TableViewToolbar.tsx';
import { useModal } from '#contexts/Modal/index.tsx';
import { useTableSearch } from '#hooks/useTableSearch.ts';
import { useListAgents } from '#modules/agents/api/queries/useListAgents.ts';
import { ImportAgentsModal } from '#modules/agents/components/import/ImportAgentsModal.tsx';
import { getAgentsProgrammingLanguages } from '#modules/agents/utils.ts';
import { isNotNull } from '#utils/helpers.ts';

import { useListProviders } from '../api/queries/useListProviders';
import { groupAgentsByProvider } from '../utils';
import { DeleteProviderButton } from './DeleteProviderButton';

export function ProvidersView() {
  const { openModal } = useModal();
  const { data: providers, isPending: isProvidersPending } = useListProviders();
  const { data: agents, isPending: isAgentsPending } = useListAgents({ onlyUiSupported: true, orderBy: 'createdAt' });
  const agentsByProvider = groupAgentsByProvider(agents);

  const entries = useMemo(
    () =>
      providers
        ? providers.items
            .map((provider) => {
              const { id, source } = provider;
              const agents = agentsByProvider[id];
              const agentsCount = agents?.length ?? 0;

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
            .filter(isNotNull)
        : [],
    [providers, agentsByProvider],
  );
  const { items: rows, onSearch } = useTableSearch({ entries, fields: ['id', 'source', 'runtime'] });
  const isPending = isProvidersPending || isAgentsPending;

  return (
    <TableView>
      <DataTable headers={HEADERS} rows={rows}>
        {({ rows, headers, getTableProps, getHeaderProps, getRowProps }) => (
          <>
            <TableViewToolbar
              searchProps={{
                onChange: onSearch,
                disabled: isPending,
              }}
              button={<Button onClick={() => openModal((props) => <ImportAgentsModal {...props} />)}>Import</Button>}
            />

            {isPending ? (
              <DataTableSkeleton headers={HEADERS} showToolbar={false} showHeader={false} />
            ) : (
              <Table {...getTableProps()}>
                <TableHead>
                  <TableRow>
                    {headers.map((header) => (
                      <TableHeader {...getHeaderProps({ header })} key={header.key}>
                        {header.header}
                      </TableHeader>
                    ))}
                  </TableRow>
                </TableHead>

                <TableBody>
                  {rows.length > 0 ? (
                    rows.map((row) => (
                      <TableRow {...getRowProps({ row })} key={row.id}>
                        {row.cells.map((cell) => (
                          <TableCell key={cell.id}>{cell.value}</TableCell>
                        ))}
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={HEADERS.length}>No results found.</TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            )}
          </>
        )}
      </DataTable>
    </TableView>
  );
}

const HEADERS = [
  { key: 'source', header: 'Source' },
  { key: 'runtime', header: 'Runtime' },
  { key: 'agents', header: <>#&nbsp;of&nbsp;agents</> },
  { key: 'actions', header: '' },
];

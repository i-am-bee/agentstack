/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { TrashCan } from '@carbon/icons-react';
import {
  Button,
  DataTable,
  DataTableSkeleton,
  IconButton,
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
import { ImportAgentsModal } from '#modules/agents/components/ImportAgentsModal.tsx';
import { getAgentsProgrammingLanguages } from '#modules/agents/utils.ts';
import { isNotNull } from '#utils/helpers.ts';

import { useDeleteProvider } from '../api/mutations/useDeleteProvider';
import { useListProviders } from '../api/queries/useListProviders';
import { groupAgentsByProvider } from '../utils';
import classes from './ProvidersView.module.scss';

export function ProvidersView() {
  const { openModal, openConfirmation } = useModal();
  const { data: providers, isPending: isProvidersPending } = useListProviders();
  const { mutate: deleteProvider } = useDeleteProvider();
  const { data: agents, isPending: isAgentsPending } = useListAgents({ onlyUiSupported: true, sort: true });
  const agentsByProvider = groupAgentsByProvider(agents);

  const entries = useMemo(
    () =>
      providers
        ? providers.items
            .map(({ id, source }) => {
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
                    <IconButton
                      label="Delete provider"
                      kind="ghost"
                      size="sm"
                      onClick={() =>
                        openConfirmation({
                          title: (
                            <>
                              Delete <span className={classes.deleteModalProviderId}>{source}</span>?
                            </>
                          ),
                          body: 'Are you sure you want to delete this provider? It can’t be undone.',
                          primaryButtonText: 'Delete',
                          danger: true,
                          onSubmit: () => deleteProvider({ id }),
                        })
                      }
                      align="left"
                    >
                      <TrashCan />
                    </IconButton>
                  </TableViewActions>
                ),
              };
            })
            .filter(isNotNull)
        : [],
    [providers, agentsByProvider, deleteProvider, openConfirmation],
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

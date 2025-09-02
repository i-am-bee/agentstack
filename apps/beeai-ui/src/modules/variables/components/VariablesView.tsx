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

import { useDeleteVariable } from '../api/mutations/useDeleteVariable';
import { useListVariables } from '../api/queries/useListVariables';
import { AddVariableModal } from './AddVariableModal';
import classes from './VariablesView.module.scss';

export function VariablesView() {
  const { openModal, openConfirmation } = useModal();
  const { data, isPending } = useListVariables();
  const { mutate: deleteVariable } = useDeleteVariable();

  const entries = useMemo(
    () =>
      data
        ? data.flatMap(({ provider, variables }) =>
            variables ? Object.entries(variables).map(([name, value]) => ({ name, value, provider })) : [],
          )
        : [],
    [data],
  );
  console.log({ data, entries });

  const { items, onSearch } = useTableSearch({ entries, fields: ['name'] });

  const rows = useMemo(() => {
    return items.map(({ provider, name, value }) => ({
      id: name,
      name,
      value,
      actions: (
        <TableViewActions>
          <IconButton
            label="Delete"
            kind="ghost"
            size="sm"
            onClick={() =>
              openConfirmation({
                title: `Delete '${name}'?`,
                body: 'Are you sure you want to delete this variable? It can’t be undone.',
                primaryButtonText: 'Delete',
                danger: true,
                onSubmit: () => deleteVariable({ providerId: provider.id, name }),
              })
            }
            align="left"
          >
            <TrashCan />
          </IconButton>
        </TableViewActions>
      ),
    }));
  }, [items, deleteVariable, openConfirmation]);

  return (
    <TableView
      description="Your variables are sensitive information and should not be shared with anyone. Keep it secure to
        prevent unauthorized access to your account."
    >
      <DataTable headers={HEADERS} rows={rows}>
        {({ rows, headers, getTableProps, getHeaderProps, getRowProps }) => (
          <>
            <TableViewToolbar
              searchProps={{
                onChange: onSearch,
                disabled: isPending,
              }}
              button={
                <Button onClick={() => openModal((props) => <AddVariableModal {...props} />)}>Add variable</Button>
              }
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
                          <TableCell key={cell.id} className={classes[cell.info.header]}>
                            {cell.value}
                          </TableCell>
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
  { key: 'name', header: 'Name' },
  { key: 'value', header: 'Value' },
  { key: 'actions', header: '' },
];

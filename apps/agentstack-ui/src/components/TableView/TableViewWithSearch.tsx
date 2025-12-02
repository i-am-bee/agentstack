/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { DataTableHeader } from '@carbon/react';
import {
  DataTable,
  DataTableSkeleton,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@carbon/react';
import type { ReactNode } from 'react';

import { useTableSearch } from '#hooks/useTableSearch.ts';

import { TableView } from './TableView.tsx';
import { TableViewToolbar } from './TableViewToolbar.tsx';

interface Props<T> {
  headers: (DataTableHeader & { className?: string })[];
  entries: T[];
  searchFields: (keyof T)[];
  toolbarButton: ReactNode;
  isPending: boolean;
  description?: string;
  emptyText?: ReactNode;
  className?: string;
}

export function TableViewWithSearch<T extends { id: string }>({
  headers,
  entries,
  searchFields,
  toolbarButton,
  isPending,
  description,
  emptyText = 'No results found.',
  className,
}: Props<T>) {
  const { items: rows, onSearch } = useTableSearch({ entries, fields: searchFields });

  const columnCount = headers.length;
  const hasRows = rows.length > 0;

  return (
    <TableView description={description} className={className}>
      <DataTable headers={headers} rows={rows}>
        {({ rows, getTableProps, getHeaderProps, getRowProps }) => (
          <>
            <TableViewToolbar searchProps={{ onChange: onSearch, disabled: isPending }} button={toolbarButton} />

            {isPending ? (
              <DataTableSkeleton headers={headers} columnCount={columnCount} showToolbar={false} showHeader={false} />
            ) : (
              <Table {...getTableProps()}>
                <TableHead>
                  <TableRow>
                    {headers.map((header) => (
                      <TableHeader {...getHeaderProps({ header })} key={header.key} className={header.className}>
                        {header.header}
                      </TableHeader>
                    ))}
                  </TableRow>
                </TableHead>

                <TableBody>
                  {hasRows ? (
                    rows.map((row) => (
                      <TableRow {...getRowProps({ row })} key={row.id}>
                        {row.cells.map((cell) => {
                          const header = headers.find(({ key }) => key === cell.info.header);

                          return (
                            <TableCell key={cell.id} className={header?.className}>
                              {cell.value}
                            </TableCell>
                          );
                        })}
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={columnCount}>{emptyText}</TableCell>
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

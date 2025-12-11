/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button } from '@carbon/react';
import { useMemo } from 'react';

import { TableViewActions } from '#components/TableView/TableViewActions.tsx';
import { TableViewWithSearch } from '#components/TableView/TableViewWithSearch.tsx';
import { useModal } from '#contexts/Modal/index.tsx';

import { useListConnectors } from '../api/queries/useListConnectors';
import { AddConnectorModal } from './AddConnectorModal';
import { ConnectorActionButton } from './ConnectorActionButton';
import classes from './ConnectorsView.module.scss';
import { DeleteConnectorButton } from './DeleteConnectorButton';

export function ConnectorsView() {
  const { openModal } = useModal();

  const { data, isPending } = useListConnectors();

  const headers = useMemo(
    () => [
      { key: 'url', header: 'URL', className: classes.url },
      { key: 'state', header: 'Status' },
      { key: 'actions', header: '' },
    ],
    [],
  );

  const entries = useMemo(() => {
    if (!data) {
      return [];
    }

    return data.items.map((item) => {
      const { id, url, state } = item;

      return {
        id,
        url,
        state,
        actions: (
          <TableViewActions>
            <ConnectorActionButton connector={item} />

            <DeleteConnectorButton connector={item} />
          </TableViewActions>
        ),
      };
    });
  }, [data]);

  return (
    <TableViewWithSearch
      className={classes.root}
      headers={headers}
      entries={entries}
      searchFields={['url']}
      isPending={isPending}
      toolbarButton={
        <Button onClick={() => openModal((props) => <AddConnectorModal {...props} />)}>Add connector</Button>
      }
    />
  );
}

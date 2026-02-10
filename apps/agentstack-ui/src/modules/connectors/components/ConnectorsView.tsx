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

  const { data: connectors, isPending } = useListConnectors();

  const headers = [
    { key: 'url', header: 'URL', className: classes.url },
    { key: 'name', header: 'Name', className: classes.name },
    { key: 'state', header: 'Status' },
    { key: 'actions', header: '' },
  ];

  const entries = useMemo(() => {
    if (!connectors) {
      return [];
    }

    return connectors.items.map((connector) => {
      const { id, url, state, metadata } = connector;

      return {
        id,
        name: metadata?.name ?? '',
        url,
        state,
        actions: (
          <TableViewActions>
            <ConnectorActionButton connector={connector} />

            <DeleteConnectorButton connector={connector} />
          </TableViewActions>
        ),
      };
    });
  }, [connectors]);

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

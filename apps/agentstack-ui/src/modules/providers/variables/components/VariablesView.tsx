/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Button } from '@carbon/react';
import { useMemo } from 'react';

import { TableViewActions } from '#components/TableView/TableViewActions.tsx';
import { TableViewWithSearch } from '#components/TableView/TableViewWithSearch.tsx';
import { useModal } from '#contexts/Modal/index.tsx';
import { isNotNull } from '#utils/helpers.ts';

import { useListAllProvidersVariables } from '../api/queries/useListAllProvidersVariables';
import { maskSecretValue } from '../utils';
import { AddVariableModal } from './AddVariableModal';
import { DeleteVariableButton } from './DeleteVariableButton';
import classes from './VariablesView.module.scss';

export function VariablesView() {
  const { openModal } = useModal();

  const { data, isPending } = useListAllProvidersVariables();

  const headers = [
    { key: 'agent', header: 'Agent', className: classes.agent },
    { key: 'name', header: 'Name', className: classes.name },
    { key: 'value', header: 'Value', className: classes.value },
    { key: 'actions', header: '' },
  ];

  const entries = useMemo(() => {
    if (!data) {
      return [];
    }

    return data
      .flatMap(({ provider, variables }) =>
        Object.entries(variables).map(([name, value]) => ({
          id: name,
          name,
          agent: provider.agent_card.name,
          value: maskSecretValue(value),
          actions: (
            <TableViewActions>
              <DeleteVariableButton provider={provider} name={name} />
            </TableViewActions>
          ),
        })),
      )
      .filter(isNotNull);
  }, [data]);

  return (
    <TableViewWithSearch
      className={classes.root}
      description="Your variables are sensitive information and should not be shared with anyone. Keep it secure to prevent unauthorized access to your account."
      headers={headers}
      entries={entries}
      searchFields={['agent', 'name']}
      isPending={isPending}
      toolbarButton={
        <Button onClick={() => openModal((props) => <AddVariableModal {...props} />)}>Add variable</Button>
      }
    />
  );
}

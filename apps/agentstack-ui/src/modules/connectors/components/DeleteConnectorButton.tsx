/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { TrashCan } from '@carbon/icons-react';
import { IconButton } from '@carbon/react';

import { Spinner } from '#components/Spinner/Spinner.tsx';
import { useModal } from '#contexts/Modal/index.tsx';

import { useDeleteConnector } from '../api/mutations/useDeleteConnector';
import type { Connector } from '../api/types';
import classes from './DeleteConnectorButton.module.scss';

interface Props {
  connector: Connector;
}

export function DeleteConnectorButton({ connector }: Props) {
  const { openConfirmation } = useModal();

  const { mutate: deleteConnector, isPending } = useDeleteConnector();

  const { id, url } = connector;

  return (
    <IconButton
      label="Delete"
      kind="ghost"
      size="sm"
      align="left"
      onClick={() =>
        openConfirmation({
          title: (
            <>
              Delete <span className={classes.url}>{url}</span>?
            </>
          ),
          body: 'Are you sure you want to delete this connector? It can’t be undone.',
          primaryButtonText: 'Delete',
          danger: true,
          onSubmit: () => deleteConnector({ connector_id: id }),
        })
      }
      disabled={isPending}
    >
      {isPending ? <Spinner center /> : <TrashCan />}
    </IconButton>
  );
}

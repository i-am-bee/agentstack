/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { TrashCan } from '@carbon/icons-react';
import { IconButton } from '@carbon/react';

import { Spinner } from '#components/Spinner/Spinner.tsx';
import { useModal } from '#contexts/Modal/index.tsx';

import classes from './DeleteButton.module.scss';

interface Props {
  entityName: string;
  entityLabel: string;
  isPending: boolean;
  onSubmit: () => void;
}

export function DeleteButton({ entityName, entityLabel, isPending, onSubmit }: Props) {
  const { openConfirmation } = useModal();

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
              Delete <span className={classes.name}>{entityName}</span>?
            </>
          ),
          body: `Are you sure you want to delete this ${entityLabel}? It can’t be undone.`,
          primaryButtonText: 'Delete',
          danger: true,
          onSubmit,
        })
      }
      disabled={isPending}
    >
      {isPending ? <Spinner center /> : <TrashCan />}
    </IconButton>
  );
}

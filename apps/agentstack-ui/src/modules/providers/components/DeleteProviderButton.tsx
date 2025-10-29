/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { TrashCan } from '@carbon/icons-react';
import { IconButton } from '@carbon/react';

import { Spinner } from '#components/Spinner/Spinner.tsx';
import { useModal } from '#contexts/Modal/index.tsx';

import { useDeleteProvider } from '../api/mutations/useDeleteProvider';
import type { Provider } from '../api/types';
import classes from './DeleteProviderButton.module.scss';

interface Props {
  provider: Provider;
}

export function DeleteProviderButton({ provider }: Props) {
  const { openConfirmation } = useModal();
  const { mutate: deleteProvider, isPending } = useDeleteProvider();

  const { id, source } = provider;

  return (
    <IconButton
      label="Delete provider"
      kind="ghost"
      size="sm"
      onClick={() =>
        openConfirmation({
          title: (
            <>
              Delete <span className={classes.source}>{source}</span>?
            </>
          ),
          body: 'Are you sure you want to delete this provider? It can’t be undone.',
          primaryButtonText: 'Delete',
          danger: true,
          onSubmit: () => deleteProvider({ id }),
        })
      }
      align="left"
      disabled={isPending}
    >
      {isPending ? <Spinner /> : <TrashCan />}
    </IconButton>
  );
}

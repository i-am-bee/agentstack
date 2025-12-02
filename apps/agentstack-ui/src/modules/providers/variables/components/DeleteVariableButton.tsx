/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { TrashCan } from '@carbon/icons-react';
import { IconButton } from '@carbon/react';

import { Spinner } from '#components/Spinner/Spinner.tsx';
import { useModal } from '#contexts/Modal/index.tsx';
import type { Provider } from '#modules/providers/api/types.ts';

import { useDeleteProviderVariable } from '../api/mutations/useDeleteProviderVariable';

interface Props {
  provider: Provider;
  name: string;
}

export function DeleteVariableButton({ provider, name }: Props) {
  const { openConfirmation } = useModal();
  const { mutate: deleteVariable, isPending } = useDeleteProviderVariable();

  return (
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
          onSubmit: () => deleteVariable({ id: provider.id, name }),
        })
      }
      align="left"
      disabled={isPending}
    >
      {isPending ? <Spinner center /> : <TrashCan />}
    </IconButton>
  );
}

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Provider } from 'agentstack-sdk';

import { DeleteButton } from '#components/DeleteButton/DeleteButton.tsx';

import { useDeleteProviderVariable } from '../api/mutations/useDeleteProviderVariable';

interface Props {
  provider: Provider;
  name: string;
}

export function DeleteVariableButton({ provider, name }: Props) {
  const { mutate: deleteVariable, isPending } = useDeleteProviderVariable();

  return (
    <DeleteButton
      entityName={name}
      entityLabel="variable"
      isPending={isPending}
      onSubmit={() => deleteVariable({ id: provider.id, name })}
    />
  );
}

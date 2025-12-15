/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Provider } from 'agentstack-sdk';

import { DeleteButton } from '#components/DeleteButton/DeleteButton.tsx';

import { useDeleteProvider } from '../api/mutations/useDeleteProvider';

interface Props {
  provider: Provider;
}

export function DeleteProviderButton({ provider }: Props) {
  const { mutate: deleteProvider, isPending } = useDeleteProvider();

  const { id, source } = provider;

  return (
    <DeleteButton
      entityName={source}
      entityLabel="provider"
      isPending={isPending}
      onSubmit={() => deleteProvider({ id })}
    />
  );
}

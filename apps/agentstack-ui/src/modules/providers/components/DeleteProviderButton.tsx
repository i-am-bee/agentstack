/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { DeleteButton } from '#components/DeleteButton/DeleteButton.tsx';

import { useDeleteProvider } from '../api/mutations/useDeleteProvider';
import type { Provider } from '../api/types';

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

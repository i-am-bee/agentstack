/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useProvider } from '#modules/providers/api/queries/useProvider.ts';
import { type Provider, ProviderStatus } from '#modules/providers/api/types.ts';

interface Props {
  providerId: string | null | undefined;
}

function getStatusHelpers(data?: Provider) {
  const status = data?.state;
  const isNotInstalled = status === ProviderStatus.Missing;
  const isStarting = status === ProviderStatus.Starting;
  const isError = status === ProviderStatus.Error;
  const isReady = status === ProviderStatus.Ready || status === ProviderStatus.Running;

  return {
    status,
    isNotInstalled,
    isStarting,
    isError,
    isReady,
  };
}

export function useProviderStatus({ providerId }: Props) {
  const query = useProvider({ id: providerId ?? undefined });

  return {
    refetch: async () => {
      const { data } = await query.refetch();

      return getStatusHelpers(data);
    },
    ...getStatusHelpers(query.data),
  };
}

export type ProviderStatusWithHelpers = ReturnType<typeof getStatusHelpers>;

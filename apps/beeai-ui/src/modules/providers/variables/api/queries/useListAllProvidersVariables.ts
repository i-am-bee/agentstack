/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQuery } from '@tanstack/react-query';

import type { QueryMetadata } from '#contexts/QueryProvider/types.ts';
import { useListProviders } from '#modules/providers/api/queries/useListProviders.ts';

import { listProviderVariables } from '..';
import { providerVariableKeys } from '../keys';

interface Props {
  errorToast?: QueryMetadata['errorToast'];
  retry?: boolean;
}

export function useListAllProvidersVariables({ errorToast, retry }: Props = {}) {
  const { data: providers } = useListProviders();

  const query = useQuery({
    queryKey: providerVariableKeys.lists(),
    queryFn: async () => {
      return Promise.all(
        providers?.items.map(async (provider) => {
          const result = await listProviderVariables({ id: provider.id });

          return { provider, variables: result?.variables ?? {} };
        }) || [],
      );
    },
    retry,
    enabled: Boolean(providers?.items.length),
    meta: {
      errorToast,
    },
  });

  return query;
}

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQuery } from '@tanstack/react-query';

import type { QueryMetadata } from '#contexts/QueryProvider/types.ts';
import { useListProviders } from '#modules/providers/api/queries/useListProviders.ts';

import { listVariables } from '..';
import { variableKeys } from '../keys';

interface Props {
  errorToast?: QueryMetadata['errorToast'];
  retry?: boolean;
}

export function useListAllVariables({ errorToast, retry }: Props = {}) {
  const { data: providers } = useListProviders();

  const query = useQuery({
    queryKey: variableKeys.lists(),
    queryFn: async () => {
      return Promise.all(
        providers?.items.map(async (provider) => {
          const result = await listVariables(provider.id);

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

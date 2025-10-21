/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useQuery } from '@tanstack/react-query';

import { readProviderBuild } from '..';
import { providerBuildKeys } from '../keys';

interface Props {
  id: string | undefined;
}

export function useProviderBuild({ id = '' }: Props) {
  const query = useQuery({
    queryKey: providerBuildKeys.detail({ id }),
    queryFn: () => readProviderBuild({ id }),
    enabled: Boolean(id),
    refetchInterval: (query) => {
      const status = query.state.data?.status;

      if (status === 'completed') {
        return false;
      }

      return 5_000;
    },
  });

  return query;
}

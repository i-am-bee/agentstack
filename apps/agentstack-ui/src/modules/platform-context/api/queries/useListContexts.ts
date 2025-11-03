/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useInfiniteQuery } from '@tanstack/react-query';

import type { ContextWithMetadata } from '#modules/platform-context/types.ts';
import { isNotNull } from '#utils/helpers.ts';

import { listContexts } from '..';
import { contextKeys } from '../keys';
import type { ListContextsParams } from '../types';

export function useListContexts(params: ListContextsParams = {}) {
  const query = useInfiniteQuery({
    queryKey: contextKeys.list(params),
    queryFn: ({ pageParam }: { pageParam?: string }) => {
      const { query } = params;

      return listContexts({
        query: {
          ...query,
          page_token: pageParam,
        },
      });
    },
    initialPageParam: undefined,
    getNextPageParam: (lastPage) =>
      lastPage?.has_more && lastPage.next_page_token ? lastPage.next_page_token : undefined,
    select: (data) => {
      const items = data.pages.flatMap((page) => page?.items).filter(isNotNull);

      return items as ContextWithMetadata[];
    },
    staleTime: 5 * 60 * 1000,
  });

  return query;
}

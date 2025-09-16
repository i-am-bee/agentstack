/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useInfiniteQuery } from '@tanstack/react-query';

import type { ListContextHistoryParams } from '#modules/platform-context/types.ts';
import { isNotNull } from '#utils/helpers.ts';

import { listContextHistory } from '..';
import { contextKeys } from '../keys';

export function useListContextHistory(params: ListContextHistoryParams) {
  const query = useInfiniteQuery({
    queryKey: contextKeys.history(params),
    queryFn: ({ pageParam }: { pageParam?: string }) => {
      const { contextId, query } = params;

      return listContextHistory({
        contextId,
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

      return items;
    },
  });

  return query;
}

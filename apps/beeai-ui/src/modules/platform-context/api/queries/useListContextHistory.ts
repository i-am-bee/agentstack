/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useInfiniteQuery } from '@tanstack/react-query';

import type { PartialBy } from '#@types/utils.ts';
import { isNotNull } from '#utils/helpers.ts';

import { listContextHistory } from '..';
import { contextKeys } from '../keys';
import type { ListContextHistoryParams, ListContextHistoryResponse } from '../types';

type Params = PartialBy<ListContextHistoryParams, 'contextId'> & {
  initialData?: ListContextHistoryResponse;
  enabled?: boolean;
  initialPageParam?: string;
};

export function useListContextHistory({
  contextId,
  query: queryParams,
  initialData,
  initialPageParam,
  enabled = true,
}: Params) {
  const query = useInfiniteQuery({
    queryKey: contextKeys.history({
      contextId: contextId!,
      query: queryParams,
    }),
    queryFn: ({ pageParam }: { pageParam?: string }) => {
      return listContextHistory({
        contextId: contextId!,
        query: {
          ...queryParams,
          page_token: pageParam,
        },
      });
    },
    initialPageParam,
    getNextPageParam: (lastPage) => {
      return lastPage?.has_more && lastPage.next_page_token ? lastPage.next_page_token : undefined;
    },
    select: (data) => {
      if (!data) {
        return undefined;
      }

      const items = data.pages.flatMap((page) => page?.items).filter(isNotNull);

      return items;
    },
    enabled: Boolean(contextId) && enabled,
    initialData: initialData ? { pages: [initialData], pageParams: [undefined] } : undefined,
  });

  return query;
}

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { useInfiniteQuery } from '@tanstack/react-query';
import type { ListContextHistoryRequest, ListContextHistoryResponse } from 'agentstack-sdk';

import type { PartialBy } from '#@types/utils.ts';
import { isNotNull } from '#utils/helpers.ts';

import { listContextHistory } from '..';
import { contextKeys } from '../keys';

type Params = PartialBy<ListContextHistoryRequest, 'context_id'> & {
  initialData?: ListContextHistoryResponse;
  enabled?: boolean;
  initialPageParam?: string;
};

export function useListContextHistory({
  context_id,
  query: queryParams,
  initialData,
  initialPageParam,
  enabled = true,
}: Params) {
  const query = useInfiniteQuery({
    queryKey: contextKeys.history({
      context_id: context_id!,
      query: queryParams,
    }),
    queryFn: ({ pageParam }: { pageParam?: string }) => {
      return listContextHistory({
        context_id: context_id!,
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
    enabled: Boolean(context_id) && enabled,
    initialData: initialData ? { pages: [initialData], pageParams: [undefined] } : undefined,
  });

  return query;
}

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { type PropsWithChildren, useEffect, useMemo } from 'react';

import { useFetchNextPage } from '#hooks/useFetchNextPage.ts';
import { useImmerWithGetter } from '#hooks/useImmerWithGetter.ts';
import { convertHistoryToUIMessages } from '#modules/history/utils.ts';
import type { UIMessage } from '#modules/messages/types.ts';
import { isAgentMessage } from '#modules/messages/utils.ts';
import { LIST_CONTEXT_HISTORY_DEFAULT_QUERY } from '#modules/platform-context/api/constants.ts';
import { useListContextHistory } from '#modules/platform-context/api/queries/useListContextHistory.ts';
import { isHistoryMessage } from '#modules/platform-context/api/utils.ts';
import { usePlatformContext } from '#modules/platform-context/contexts/index.ts';
import { isNotNull } from '#utils/helpers.ts';

import { MessagesContext } from './messages-context';

export function MessagesProvider({ children }: PropsWithChildren) {
  const { contextId, history: initialHistory } = usePlatformContext();

  const { data: history, ...queryRest } = useListContextHistory({
    contextId: contextId ?? undefined,
    query: LIST_CONTEXT_HISTORY_DEFAULT_QUERY,
    initialData: initialHistory,
    // Ensures newly created messages are not fetched from history
    initialPageParam: initialHistory?.next_page_token ?? undefined,
    // Ensures history is not fetched for newly created contexts, where previous rule isn't sufficient to prevent message duplication
    enabled: Boolean(initialHistory),
  });

  const [messages, getMessages, setMessages] = useImmerWithGetter<UIMessage[]>(
    convertHistoryToUIMessages(history ?? []),
  );

  useEffect(() => {
    if (history) {
      setMessages((messages) => {
        const messageIds = new Set(messages.map(({ id }) => id));
        const artifactIds = new Set(
          messages.map((message) => (isAgentMessage(message) ? message.artifactId : null)).filter(isNotNull),
        );

        const newItems = history.filter(({ data }) =>
          isHistoryMessage(data) ? !messageIds.has(data.messageId) : !artifactIds.has(data.artifactId),
        );

        messages.push(...convertHistoryToUIMessages(newItems));
      });
    }
  }, [history, setMessages]);

  const { fetchNextPage, isFetching, hasNextPage } = queryRest;
  const { ref: fetchNextPageInViewAnchorRef } = useFetchNextPage({
    fetchNextPage,
    isFetching,
    hasNextPage,
  });

  const value = useMemo(
    () => ({
      messages,
      getMessages,
      setMessages,
      queryControl: {
        ...queryRest,
        fetchNextPageInViewAnchorRef,
      },
    }),
    [messages, getMessages, setMessages, queryRest, fetchNextPageInViewAnchorRef],
  );

  return <MessagesContext.Provider value={value}>{children}</MessagesContext.Provider>;
}

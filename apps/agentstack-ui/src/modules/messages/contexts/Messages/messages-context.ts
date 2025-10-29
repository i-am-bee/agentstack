/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use client';

import { createContext } from 'react';

import type { Updater } from '#hooks/useImmerWithGetter.ts';
import type { UIMessage } from '#modules/messages/types.ts';
import type { useListContextHistory } from '#modules/platform-context/api/queries/useListContextHistory.ts';

export const MessagesContext = createContext<MessagesContextValue | null>(null);

export interface MessagesContextValue {
  messages: UIMessage[];
  isLastMessage: (message: UIMessage) => boolean;
  getMessages: () => UIMessage[];
  setMessages: Updater<UIMessage[]>;
  queryControl: {
    fetchNextPageInViewAnchorRef: (node?: Element | null) => void;
  } & Omit<ReturnType<typeof useListContextHistory>, 'data'>;
}

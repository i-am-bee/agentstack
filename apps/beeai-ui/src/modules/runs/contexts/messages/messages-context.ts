/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { createContext } from 'react';

import type { Updater } from '#hooks/useImmerWithGetter.ts';
import type { ChatMessage } from '#modules/runs/chat/types.ts';
import { noop } from '#utils/helpers.ts';

export const MessagesContext = createContext<MessagesContextValue>({
  messages: [],
  setMessages: noop,
});

type MessagesContextValue = {
  messages: ChatMessage[];
  setMessages: Updater<ChatMessage[]>;
};

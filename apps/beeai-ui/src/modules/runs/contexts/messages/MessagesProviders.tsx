/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { type PropsWithChildren, useMemo } from 'react';

import { useImmerWithGetter } from '#hooks/useImmerWithGetter.ts';
import type { ChatMessage } from '#modules/runs/chat/types.ts';

import { MessagesContext } from './messages-context';

export function MessagesProvider({ children }: PropsWithChildren) {
  const [messages, , setMessages] = useImmerWithGetter<ChatMessage[]>([]);

  const value = useMemo(() => ({ messages, setMessages }), [messages, setMessages]);

  return <MessagesContext.Provider value={value}>{children}</MessagesContext.Provider>;
}

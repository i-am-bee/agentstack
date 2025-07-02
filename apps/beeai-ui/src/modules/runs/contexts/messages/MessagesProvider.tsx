/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { PropsWithChildren } from 'react';

import type { ChatMessage } from '#modules/runs/chat/types.ts';

import { MessagesContext } from './messages-context';

interface Props {
  messages: ChatMessage[];
}

export function MessagesProvider({ messages, children }: PropsWithChildren<Props>) {
  return <MessagesContext.Provider value={{ messages }}>{children}</MessagesContext.Provider>;
}

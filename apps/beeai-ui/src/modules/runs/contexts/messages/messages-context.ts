/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use client';

import { createContext } from 'react';

import type { ChatMessage } from '#modules/runs/chat/types.ts';

export const MessagesContext = createContext<MessagesContextValue>({ messages: [] });

type MessagesContextValue = {
  messages: ChatMessage[];
};

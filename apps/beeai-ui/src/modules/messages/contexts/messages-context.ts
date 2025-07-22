/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */
'use client';

import { createContext } from 'react';

import type { UIMessage } from '#modules/messages/types.ts';

export const MessagesContext = createContext<MessagesContextValue>({ messages: [] });

type MessagesContextValue = {
  messages: UIMessage[];
};

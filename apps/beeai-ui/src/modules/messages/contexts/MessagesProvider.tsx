/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { PropsWithChildren } from 'react';

import type { MessagesContextValue } from './messages-context';
import { MessagesContext } from './messages-context';

export function MessagesProvider({ messages, children }: PropsWithChildren<MessagesContextValue>) {
  return <MessagesContext.Provider value={{ messages }}>{children}</MessagesContext.Provider>;
}

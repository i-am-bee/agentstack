/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { use } from 'react';

import { MessagesContext } from './messages-context';

export function useMessages() {
  const context = use(MessagesContext);

  if (!context) {
    throw new Error('useMessages must be used within a MessagesProvider');
  }

  return context;
}

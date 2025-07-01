/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { createContext } from 'react';

import type { Agent } from '#modules/agents/api/types.ts';

export const ChatContext = createContext<ChatContextValue | null>(null);

interface ChatContextValue {
  agent: Agent;
  isPending: boolean;
  onClear: () => void;
  onCancel: () => void;
  sendMessage: (input: string) => Promise<void>;
}

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { ChatMessage } from '../chat/types';
import { isAgentMessage } from '../utils';

export function getHandsOffOutput(messages: ChatMessage[] | undefined) {
  const output = messages?.find(isAgentMessage)?.content;

  return output;
}

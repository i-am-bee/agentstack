/**
 * Copyright 2026 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Message } from '@a2a-js/sdk';

export function extractTextFromMessage(message: Message | undefined) {
  const text = message?.parts
    .filter((part) => part.kind === 'text')
    .map((part) => part.text)
    .join('\n');

  return text;
}

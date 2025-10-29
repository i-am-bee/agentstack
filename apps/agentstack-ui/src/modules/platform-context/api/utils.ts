/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { HistoryItem, HistoryMessage } from './types';

export function isHistoryMessage(item: HistoryItem): item is HistoryMessage {
  return 'kind' in item && item.kind === 'message';
}

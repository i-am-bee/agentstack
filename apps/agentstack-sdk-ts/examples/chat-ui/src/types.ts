/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Client } from '@a2a-js/sdk/client';

export interface Session {
  client: Client;
  contextId: string;
  metadata: Record<string, unknown>;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'agent';
  text: string;
}

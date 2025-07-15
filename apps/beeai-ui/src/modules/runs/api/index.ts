/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { MessageSendParams, TaskIdParams } from '@a2a-js/sdk';
import { A2AClient } from '@a2a-js/sdk/client';

export async function sendMessageStream(client: A2AClient, params: MessageSendParams) {
  return client.sendMessageStream(params);
}

export async function cancelTask(client: A2AClient, params: TaskIdParams) {
  return await client.cancelTask(params);
}

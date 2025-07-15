/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { MessageSendParams } from '@a2a-js/sdk';
import { A2AClient } from '@a2a-js/sdk/client';
import type { RunId } from 'acp-sdk';

import { acp } from '#acp/index.ts';

export async function createRunStream(client: A2AClient, params: MessageSendParams) {
  return await client.sendMessageStream(params);
}

export async function readRun(runId: RunId) {
  return await acp.runStatus(runId);
}

export async function cancelRun(runId: RunId) {
  return await acp.runCancel(runId);
}

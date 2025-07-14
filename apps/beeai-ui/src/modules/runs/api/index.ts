/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { MessageSendParams } from '@a2a-js/sdk';
import type { RunId } from 'acp-sdk';

import { a2a } from '#a2a/index.ts';
import { acp } from '#acp/index.ts';

export async function createRunStream(params: MessageSendParams) {
  return await a2a.sendMessageStream(params);
}

export async function readRun(runId: RunId) {
  return await acp.runStatus(runId);
}

export async function cancelRun(runId: RunId) {
  return await acp.runCancel(runId);
}

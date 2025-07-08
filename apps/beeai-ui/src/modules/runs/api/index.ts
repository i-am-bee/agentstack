/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { AgentName, RunId } from 'acp-sdk';
import type { Input } from 'acp-sdk/client/types';

import { acp } from '#acp/index.ts';

interface CreateRunStreamParams {
  agentName: AgentName;
  input: Input;
  sessionId?: string;
}

export async function createRunStream({ body, signal }: { body: CreateRunStreamParams; signal?: AbortSignal }) {
  return await acp.withSession(
    async (session) => session.runStream(body.agentName, body.input, signal),
    body.sessionId,
  );
}

export async function readRun(runId: RunId) {
  return await acp.runStatus(runId);
}

export async function cancelRun(runId: RunId) {
  return await acp.runCancel(runId);
}

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { events } from 'fetch-event-stream';

import { api } from '#api/index.ts';
import { ensureData, ensureResponse } from '#api/utils.ts';

import type { CancelRunPath, CreateRunStreamRequest, ReadRunPath, ResumeRunPath, ResumeRunRequest } from './types';

export async function createRunStream({ body, signal }: { body: CreateRunStreamRequest; signal?: AbortSignal | null }) {
  const response = await api.POST('/api/v1/acp/runs', { parseAs: 'stream', body, signal });
  const stream = events(ensureResponse(response), signal);

  return stream;
}

export async function readRun({ run_id }: ReadRunPath) {
  const response = await api.GET('/api/v1/acp/runs/{run_id}', { params: { path: { run_id } } });

  return ensureData(response);
}

export async function resumeRun({ run_id, body }: ResumeRunPath & { body: ResumeRunRequest }) {
  const response = await api.POST('/api/v1/acp/runs/{run_id}', { params: { path: { run_id } }, body });

  return ensureData(response);
}

export async function cancelRun({ run_id }: CancelRunPath) {
  const response = await api.POST('/api/v1/acp/runs/{run_id}/cancel', { params: { path: { run_id } } });

  return ensureData(response);
}

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { z } from 'zod';

import type { A2AExtension } from '#api/a2a/extensions/types.ts';

const URI = 'beeai-sequential-workflow';

const schema = z
  .object({
    agent_name: z.string(),
    provider_id: z.string(),
    agent_idx: z.number(),
    message: z.string(),
  })
  .partial();

export type SequentialWorkflowMetadata = z.infer<typeof schema>;

export const sequentialWorkflowExtension: A2AExtension<typeof URI, SequentialWorkflowMetadata> = {
  getSchema: () => z.object({ [URI]: schema }).partial(),
  getUri: () => URI,
};

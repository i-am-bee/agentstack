/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { z } from 'zod';

import type { A2AExtension } from './types';

const URI = 'https://a2a-extensions.beeai.dev/ui/trajectory/v1';

const schema = z
  .object({
    message: z.string(),
    tool_name: z.string(),
    tool_input: z.record(z.string(), z.unknown()),
    tool_outpyut: z.record(z.string(), z.unknown()),
  })
  .partial();

export type TrajectoryMetadata = z.infer<typeof schema>;

export const trajectoryExtension: A2AExtension<typeof URI, TrajectoryMetadata> = {
  getSchema: () => z.object({ [URI]: schema }).partial(),
  getUri: () => URI,
};

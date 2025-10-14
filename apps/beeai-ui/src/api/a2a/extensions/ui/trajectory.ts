/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { A2AUiExtension } from 'beeai-sdk';
import { z } from 'zod';

const URI = 'https://a2a-extensions.beeai.dev/ui/trajectory/v1';

const schema = z
  .object({
    title: z.string(),
    content: z.string(),
  })
  .partial();

export type TrajectoryMetadata = z.infer<typeof schema>;

export const trajectoryExtension: A2AUiExtension<typeof URI, TrajectoryMetadata> = {
  getMessageMetadataSchema: () => z.object({ [URI]: schema }).partial(),
  getUri: () => URI,
};

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { z } from 'zod';

import type { A2AUiExtension } from '../types';

const URI = 'https://a2a-extensions.agentstack.beeai.dev/ui/canvas/v1';

const schema = z.object({
  start_index: z.int(),
  end_index: z.int(),
  description: z.string().nullish(),
  artifact_id: z.string(),
});

export type CanvasEditRequest = z.infer<typeof schema>;

export const CanvasExtension: A2AUiExtension<typeof URI, CanvasEditRequest> = {
  getMessageMetadataSchema: () => z.object({ [URI]: schema }).partial(),
  getUri: () => URI,
};

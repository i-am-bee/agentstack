/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { z } from 'zod';

import type { A2AUiExtension } from '../types';

const URI = 'https://a2a-extensions.agentstack.beeai.dev/ui/canvas/v1';

const responseSchema = z.object({
  start_index: z.int(),
  end_index: z.int(),
  description: z.string().nullish(),
  artifact_id: z.string(),
});

export type CanvasFulfillments = z.infer<typeof responseSchema>;

export const canvasExtension: A2AUiExtension<typeof URI, CanvasFulfillments> = {
  getMessageMetadataSchema: () => z.object({ [URI]: responseSchema }).partial(),
  getUri: () => URI,
};

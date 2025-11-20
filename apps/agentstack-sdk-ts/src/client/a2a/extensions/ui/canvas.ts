/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { z } from 'zod';

import type { A2AServiceExtension } from '../types';

const URI = 'https://a2a-extensions.agentstack.beeai.dev/ui/canvas/v1';

const schema = z.null();

export type CanvasMetadata = z.infer<typeof schema>;

const responseSchema = z.object({
  start_index: z.int(),
  end_index: z.int(),
  description: z.string().nullish(),
  artifact_id: z.string(),
});

type CanvasFulfillments = z.infer<typeof responseSchema>;

export const canvasExtension: A2AServiceExtension<typeof URI, z.infer<typeof schema>, CanvasFulfillments> = {
  getDemandsSchema: () => schema,
  getFulfillmentSchema: () => responseSchema,
  getUri: () => URI,
};

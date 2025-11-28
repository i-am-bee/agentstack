/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

import type { A2AUiExtension } from '../types';

const URI = 'https://a2a-extensions.agentstack.beeai.dev/ui/error/v1';

const errorSchema = z.object({
  title: z.string(),
  message: z.string(),
});

const errorGroupSchema = z.object({
  message: z.string(),
  errors: z.array(errorSchema),
});

const schema = z.object({
  error: z.union([errorSchema, errorGroupSchema]),
  context: z.record(z.string(), z.unknown()).nullish(),
  stack_trace: z.string().nullish(),
});

export type ErrorMetadata = z.infer<typeof schema>;

export const errorExtension: A2AUiExtension<typeof URI, ErrorMetadata> = {
  getMessageMetadataSchema: () => z.object({ [URI]: schema }).partial(),
  getUri: () => URI,
};

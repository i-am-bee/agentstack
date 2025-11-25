/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

import type { A2AUiExtension } from '../types';

const URI = 'https://a2a-extensions.agentstack.beeai.dev/ui/error/v1';

const schema = z.object({
  message: z.string(),
  title: z.string().nullish(),
  context: z.record(z.string(), z.unknown()).nullish(),
  stacktrace: z.string().nullish(),
});

export type ErrorMetadata = z.infer<typeof schema>;

export const errorExtension: A2AUiExtension<typeof URI, ErrorMetadata> = {
  getMessageMetadataSchema: () => z.object({ [URI]: schema }).partial(),
  getUri: () => URI,
};

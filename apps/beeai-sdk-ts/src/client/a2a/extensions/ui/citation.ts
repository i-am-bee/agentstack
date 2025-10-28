/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { z } from 'zod';

import type { A2AUiExtension } from '../types';

const URI = 'https://a2a-extensions.beeai.dev/ui/citation/v1';

const citationSchema = z.object({
  url: z.string().nullish(),
  start_index: z.number().nullish(),
  end_index: z.number().nullish(),
  title: z.string().nullish(),
  description: z.string().nullish(),
});

const schema = z.object({
  citations: z.array(citationSchema),
});

export type CitationMetadata = z.infer<typeof schema>;
export type Citation = z.infer<typeof citationSchema>;

export const citationExtension: A2AUiExtension<typeof URI, CitationMetadata> = {
  getMessageMetadataSchema: () => z.object({ [URI]: schema }).partial(),
  getUri: () => URI,
};

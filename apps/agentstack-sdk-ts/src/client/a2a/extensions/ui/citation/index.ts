/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

import type { A2AUiExtension } from '../../../../core/extensions/types';
import { citationMetadataSchema } from './schemas';
import type { CitationMetadata } from './types';

export const CITATION_EXTENSION_URI = 'https://a2a-extensions.agentstack.beeai.dev/ui/citation/v1';

export const citationExtension: A2AUiExtension<typeof CITATION_EXTENSION_URI, CitationMetadata> = {
  getUri: () => CITATION_EXTENSION_URI,
  getMessageMetadataSchema: () => z.object({ [CITATION_EXTENSION_URI]: citationMetadataSchema }).partial(),
};

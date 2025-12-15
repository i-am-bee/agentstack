/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

import type { A2AUiExtension } from '../../../../core/extensions/types';
import { errorMetadataSchema } from './schemas';
import type { ErrorMetadata } from './types';

const URI = 'https://a2a-extensions.agentstack.beeai.dev/ui/error/v1';

export const errorExtension: A2AUiExtension<typeof URI, ErrorMetadata> = {
  getUri: () => URI,
  getMessageMetadataSchema: () => z.object({ [URI]: errorMetadataSchema }).partial(),
};

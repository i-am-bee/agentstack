/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

import type { A2AUiExtension } from '../../../../core/extensions/types';
import { streamingMessageSchema } from './schemas';
import type { StreamingMessage } from './types';

export const STREAMING_EXTENSION_URI = 'https://a2a-extensions.agentstack.beeai.dev/ui/streaming/v1';

export const streamingExtension: A2AUiExtension<typeof STREAMING_EXTENSION_URI, StreamingMessage> = {
  getUri: () => STREAMING_EXTENSION_URI,
  getMessageMetadataSchema: () => z.object({ [STREAMING_EXTENSION_URI]: streamingMessageSchema }).partial(),
};

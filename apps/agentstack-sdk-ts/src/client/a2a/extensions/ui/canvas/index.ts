/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

import type { A2AUiExtension } from '../../../../core/extensions/types';
import { canvasEditRequestSchema } from './schemas';
import type { CanvasEditRequest } from './types';

const URI = 'https://a2a-extensions.agentstack.beeai.dev/ui/canvas/v1';

export const canvasExtension: A2AUiExtension<typeof URI, CanvasEditRequest> = {
  getUri: () => URI,
  getMessageMetadataSchema: () => z.object({ [URI]: canvasEditRequestSchema }).partial(),
};

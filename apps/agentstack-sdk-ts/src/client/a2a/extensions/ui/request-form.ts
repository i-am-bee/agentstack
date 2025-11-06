/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { z } from 'zod';

import type { A2AUiExtension } from '../types';
import { formRenderSchema } from '../common/form';

const URI = 'https://a2a-extensions.agentstack.beeai.dev/ui/request_form/v1';

export type FormRequest = z.infer<typeof formRenderSchema>;

export const requestFormExtension: A2AUiExtension<typeof URI, FormRequest> = {
  getMessageMetadataSchema: () => z.object({ [URI]: formRenderSchema }).partial(),
  getUri: () => URI,
};

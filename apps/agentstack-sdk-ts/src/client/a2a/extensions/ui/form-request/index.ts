/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import z from 'zod';

import type { A2AUiExtension } from '../../../../core/extensions/types';
import { formRenderSchema } from '../../common/form/schemas';
import type { FormRender } from '../../common/form/types';

export const FORM_REQUEST_EXTENSION_URI = 'https://a2a-extensions.agentstack.beeai.dev/ui/form_request/v1';

export const formRequestExtension: A2AUiExtension<typeof FORM_REQUEST_EXTENSION_URI, FormRender> = {
  getUri: () => FORM_REQUEST_EXTENSION_URI,
  getMessageMetadataSchema: () => z.object({ [FORM_REQUEST_EXTENSION_URI]: formRenderSchema }).partial(),
};

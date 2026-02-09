/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { approvalResponseExtension } from '../../a2a/extensions/interactions/approval';
import { GENERATIVE_INTERFACE_EXTENSION_URI } from '../../a2a/extensions/services/generative-interface';
import { canvasExtension } from '../../a2a/extensions/ui/canvas';
import { formRequestExtension } from '../../a2a/extensions/ui/form-request';
import type { UserMetadataInputs } from './types';

export const resolveUserMetadata = async (inputs: UserMetadataInputs) => {
  const metadata: Record<string, unknown> = {};

  const { form, canvasEditRequest, approvalResponse, generativeInterfaceResponse } = inputs;

  if (form) {
    metadata[formRequestExtension.getUri()] = {
      values: form,
    };
  }
  if (canvasEditRequest) {
    metadata[canvasExtension.getUri()] = canvasEditRequest;
  }
  if (approvalResponse) {
    metadata[approvalResponseExtension.getUri()] = approvalResponse;
  }
  if (generativeInterfaceResponse) {
    metadata[GENERATIVE_INTERFACE_EXTENSION_URI] = generativeInterfaceResponse;
  }

  return metadata;
};

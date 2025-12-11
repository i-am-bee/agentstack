/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { FormResponseValue } from './common/form';
import { type CanvasEditRequest, CanvasExtension } from './ui/canvas';
import { FormRequestExtension } from './ui/form-request';

export type UserMetadataInputs = Partial<{
  form: Record<string, FormResponseValue>;
  canvasEditRequest: CanvasEditRequest;
}>;

export const resolveUserMetadata = async (inputs: UserMetadataInputs) => {
  const metadata: Record<string, unknown> = {};

  const { form, canvasEditRequest } = inputs;

  if (form) {
    metadata[FormRequestExtension.getUri()] = {
      values: form,
    };
  }
  if (canvasEditRequest) {
    metadata[CanvasExtension.getUri()] = canvasEditRequest;
  }

  return metadata;
};

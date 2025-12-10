/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { FormResponseValue } from './common/form';
import { type CanvasEditRequest, CanvasExtension } from './ui/canvas';
import { FormRequestExtension } from './ui/form-request';

export type UiExtensionInputs = Partial<{
  form: Record<string, FormResponseValue>;
  canvasEditRequest: CanvasEditRequest;
}>;

export const handleUiExtensionInput = () => {
  const resolveMetadata = async (inputs: UiExtensionInputs) => {
    const metadata: Record<string, unknown> = {};

    if (inputs.form) {
      metadata[FormRequestExtension.getUri()] = {
        values: inputs.form,
      };
    }
    if (inputs.canvasEditRequest) {
      metadata[CanvasExtension.getUri()] = inputs.canvasEditRequest;
    }

    return metadata;
  };

  return {
    resolveMetadata,
  };
};

/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { FormResponseValue } from './common/form';
import { FormRequestExtension } from './ui/form-request';

export type InputRequiredResponses = Partial<{
  form: Record<string, FormResponseValue>;
}>;

export const handleInputRequired = () => {
  const resolveMetadata = async (responses: InputRequiredResponses) => {
    const metadata: Record<string, unknown> = {};

    if (responses.form) {
      metadata[FormRequestExtension.getUri()] = {
        values: responses.form,
      };
    }

    return metadata;
  };

  return {
    resolveMetadata,
  };
};

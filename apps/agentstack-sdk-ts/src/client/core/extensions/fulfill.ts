/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { A2AServiceExtension } from './types';

export function fulfillServiceExtensionDemand<U extends string, D, F>(extension: A2AServiceExtension<U, D, F>) {
  const schema = extension.getFulfillmentsSchema();
  const uri = extension.getUri();

  return function (metadata: Record<string, unknown>, fulfillment: F) {
    const { success, data: parsed, error } = schema.safeParse(fulfillment);

    if (!success) {
      console.warn(error);
    }

    return {
      ...metadata,
      [uri]: success ? parsed : {},
    };
  };
}

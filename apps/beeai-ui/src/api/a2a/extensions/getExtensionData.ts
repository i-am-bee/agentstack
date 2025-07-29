/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { A2AExtension } from './a2aExtension';

export function getExtensionData<U extends string, D>(extension: A2AExtension<U, D>) {
  const schema = extension.getSchema();
  const uri = extension.getUri();

  return function (metadata: Record<string, unknown> | undefined) {
    const { success, data: parsed } = schema.safeParse(metadata ?? {});

    if (!success) {
      return undefined;
    }

    return parsed[uri];
  };
}

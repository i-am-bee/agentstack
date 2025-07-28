/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type { A2AExtension } from './a2aExtension';

export const getExtensionData =
  <T extends string, D>(extension: A2AExtension<T, D>) =>
  (metadata: Record<string, unknown> | undefined) => {
    const parsed = extension.getSchema().parse(metadata || {});
    if (parsed[extension.getKey()]) {
      return parsed[extension.getKey()];
    }

    return undefined;
  };

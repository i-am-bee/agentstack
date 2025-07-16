/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { defaultUrlTransform } from 'react-markdown';

export function urlTransform(value: string): string {
  if (value.startsWith('data:image/')) {
    return value;
  }

  return defaultUrlTransform(value);
}

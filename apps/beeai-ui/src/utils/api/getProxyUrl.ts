/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { BASE_PATH } from '#utils/constants.ts';

export function createProxyUrl(url: string) {
  try {
    const { origin } = new URL(url);

    return BASE_PATH + url.replace(origin, '');
  } catch {
    return url;
  }
}

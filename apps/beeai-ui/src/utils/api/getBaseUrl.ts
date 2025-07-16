/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { API_URL, BASE_PATH } from '#utils/constants.ts';

export function getBaseUrl(suffix = '') {
  const baseUrl = typeof window !== 'undefined' ? BASE_PATH : API_URL;
  return baseUrl + suffix;
}

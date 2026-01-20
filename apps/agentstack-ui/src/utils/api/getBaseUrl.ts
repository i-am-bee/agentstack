/**
 * Copyright 2025 © BeeAI a Series of LF Projects, LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { API_URL, BASE_PATH } from '#utils/constants.ts';

export function getBaseUrl() {
  const isClient = typeof window !== 'undefined';
  const baseUrl = isClient ? new URL(BASE_PATH, window.location.origin).toString() : API_URL;

  return baseUrl;
}
